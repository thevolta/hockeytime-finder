from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from hashlib import sha1
import re
from typing import List, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, Tag

from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


AZ_TZ = ZoneInfo("America/Phoenix")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

ROW_RE = re.compile(
    r"(?P<dow>Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<start>\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*"
    r"(?P<end>\d{1,2}:\d{2}\s*(?:am|pm))\s+"
    r"(?P<title>.+?)(?=\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}/|\s+Show more events|$)",
    re.I,
)


def classify(text: str) -> Optional[str]:
    lowered = text.lower()
    if "adult skills" in lowered or "adult hockey skills" in lowered:
        return "Adult Skills"
    if "flow hockey" in lowered:
        return "Flow Hockey"
    if (
        "open hockey" in lowered
        or "pickup hockey" in lowered
        or "pick up hockey" in lowered
    ):
        return "Open Hockey"
    if "stick time" in lowered or "sticktime" in lowered:
        return "Stick Time"
    return None


def clean_title(text: str) -> str:
    text = re.sub(r"\bRegister Online\b", "", text, flags=re.I)
    text = re.sub(r"\s+Show more events.*$", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip(" |-") or "Hockey Event"


class SportifiedProvider(BaseProvider):
    def _page_sources(self):
        return self.source.get("pages") or [
            {
                "url": "https://mullett.sportified.net/pages/hockey/sticktime",
                "event_type": "Stick Time",
            },
            {
                "url": "https://mullett.sportified.net/pages/hockey/adult-open-hockey",
                "event_type": "Open Hockey",
            },
            {
                "url": "https://mullett.sportified.net/pages/hockey/flow-hockey",
                "event_type": "Flow Hockey",
            },
        ]

    def _fetch_page(self, url: str) -> BeautifulSoup:
        response = requests.get(url, timeout=8, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def parse_registration_options(soup: BeautifulSoup) -> list[dict]:
        """Read Sportified product option rows (not the public roster)."""
        options = []
        form = soup.select_one("form#register-form")
        if form is None:
            return options
        for row in form.select("table tbody tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 3:
                continue
            name_node = cells[0].select_one(".title")
            availability_node = cells[1].select_one(".availability")
            if name_node is None or availability_node is None:
                continue
            name = " ".join(name_node.stripped_strings).strip()
            match = re.search(r"(\d+)\s+of\s+(\d+)\s+available", " ".join(availability_node.stripped_strings), re.I)
            if not name or not match:
                continue
            available, capacity = map(int, match.groups())
            price = " ".join(cells[2].stripped_strings).strip()
            link = row.select_one('a[href*="/variants/"]')
            options.append({
                "name": name,
                "registered": max(0, capacity - available),
                "capacity": capacity,
                "available": available,
                "price": price,
                "register_url": urljoin("https://mullett.sportified.net", link["href"]) if link else None,
            })
        return options

    def _attach_registration_options(self, events: list[HockeyEvent]):
        """Fetch product pages once per URL during the scheduled refresh."""
        cached: dict[str, list[dict]] = {}
        for event in events:
            url = event.register_url or ""
            if not re.search(r"mullett\.sportified\.net/products/\d+", url):
                continue
            if url not in cached:
                try:
                    cached[url] = self.parse_registration_options(self._fetch_page(url))
                except requests.RequestException:
                    cached[url] = []
            event.registration_options = cached[url]
            if cached[url]:
                event.capacity = sum(item["capacity"] for item in cached[url])
                event.registered_count = sum(item["registered"] for item in cached[url])
                event.open_slots = sum(item["available"] for item in cached[url])

    def _row_nodes(self, soup: BeautifulSoup):
        table_rows = []
        for tr in soup.find_all("tr"):
            text = " ".join(tr.stripped_strings)
            if ROW_RE.search(text):
                table_rows.append((tr, text))

        # If the page has actual rows, use only those. This prevents parent divs
        # from producing duplicate/combined events.
        if table_rows:
            yield from table_rows
            return

        # Fallback: choose only the smallest matching nodes.
        matches = []
        for node in soup.find_all(["li", "p", "div"]):
            text = " ".join(node.stripped_strings)
            if len(text) <= 260 and ROW_RE.search(text):
                matches.append((node, text))

        for node, text in matches:
            child_has_match = any(
                ROW_RE.search(" ".join(child.stripped_strings))
                for child in node.find_all(["li", "p", "div"], recursive=False)
            )
            if not child_has_match:
                yield node, text

    def fetch_events(self) -> List[HockeyEvent]:
        now = datetime.now(AZ_TZ)
        events: list[HockeyEvent] = []
        seen: set[tuple] = set()

        for page in self._page_sources():
            page_url = page["url"]
            soup = self._fetch_page(page_url)

            for node, text in self._row_nodes(soup):
                match = ROW_RE.search(text)
                if not match:
                    continue

                event_type = page.get("event_type") or classify(match.group("title"))
                title = clean_title(match.group("title"))
                if event_type == "Adult Skills" and "skill" not in title.lower():
                    title = "Adult Skills"

                date_text = match.group("date")
                fmt = "%m/%d/%Y" if len(date_text.split("/")[-1]) == 4 else "%m/%d/%y"
                event_date = datetime.strptime(date_text, fmt).date()

                start_time = datetime.strptime(
                    match.group("start").lower().replace(" ", ""),
                    "%I:%M%p",
                ).time()
                end_time = datetime.strptime(
                    match.group("end").lower().replace(" ", ""),
                    "%I:%M%p",
                ).time()

                start = datetime.combine(event_date, start_time, tzinfo=AZ_TZ)
                end = datetime.combine(event_date, end_time, tzinfo=AZ_TZ)
                if end <= start:
                    end += timedelta(days=1)
                if end < now - timedelta(hours=2):
                    continue

                register_url = None
                if isinstance(node, Tag):
                    for anchor in node.find_all("a", href=True):
                        label = " ".join(anchor.stripped_strings).lower()
                        href = anchor.get("href", "")
                        if "register" in label or "/products/" in href:
                            register_url = urljoin(page_url, href)
                            break

                # De-dupe by event type + exact time rather than title. That
                # suppresses combined parent blocks even if their title differs.
                key = (event_type, start.isoformat(), end.isoformat())
                if key in seen:
                    continue
                seen.add(key)

                uid_src = f"{self.source['name']}|{event_type}|{start.isoformat()}"
                uid = sha1(uid_src.encode()).hexdigest()[:16]

                events.append(
                    HockeyEvent(
                        id=uid,
                        title=title,
                        event_type=event_type,
                        rink=self.source["name"],
                        city=self.source.get("city"),
                        state=self.source.get("state"),
                        start=start,
                        end=end,
                        register_url=(page_url if event_type == "Adult Skills" else (register_url or page_url)),
                        source_url=page_url,
                        provider="sportified",
                        last_updated=datetime.now(timezone.utc),
                    )
                )

        events.extend(self._fetch_schedule_skills(now, seen))
        self._attach_registration_options(events)
        events.sort(key=lambda event: event.start)
        return events

    def _fetch_schedule_skills(self, now, seen):
        """Parse Sportified's actual day-grouped schedule tables."""
        found = []
        for offset in (0, 7, 14, 21, 28):
            date = (now + timedelta(days=offset)).date().isoformat()
            url = f"https://mullett.sportified.net/schedule?date={date}"
            try:
                soup = self._fetch_page(url)
            except requests.RequestException:
                continue

            for table in soup.select("table.ui.celled.striped.table"):
                heading = table.select_one("thead th")
                if heading is None:
                    continue
                heading_text = " ".join(heading.stripped_strings)
                try:
                    event_date = datetime.strptime(
                        re.sub(r"\s+", " ", heading_text), "%A, %B %d %Y"
                    ).date()
                except ValueError:
                    continue

                for row in table.select("tbody tr"):
                    cells = row.find_all("td", recursive=False)
                    if len(cells) != 3:
                        continue
                    title_node = cells[1]
                    title = clean_title(" ".join(title_node.stripped_strings))
                    if not ("adult rookie class" in title.lower() or "adult skills" in title.lower()):
                        continue
                    time_text = " ".join(cells[0].stripped_strings)
                    match = re.search(
                        r"(\d{1,2}:\d{2}\s*[ap]m)\s*-\s*(\d{1,2}:\d{2}\s*[ap]m)",
                        time_text, re.I,
                    )
                    if not match:
                        continue
                    start_t = datetime.strptime(match.group(1).replace(" ", "").lower(), "%I:%M%p").time()
                    end_t = datetime.strptime(match.group(2).replace(" ", "").lower(), "%I:%M%p").time()
                    start = datetime.combine(event_date, start_t, tzinfo=AZ_TZ)
                    end = datetime.combine(event_date, end_t, tzinfo=AZ_TZ)
                    if end <= start:
                        end += timedelta(days=1)
                    if end < now - timedelta(hours=2):
                        continue
                    event_type = "Adult Skills"
                    key = (event_type, start.isoformat(), end.isoformat())
                    if key in seen:
                        continue
                    seen.add(key)
                    link = title_node.select_one('a[href*="/products/"]')
                    register_url = urljoin(url, link["href"]) if link else url
                    uid = sha1(f"{self.source['name']}|{event_type}|{start.isoformat()}".encode()).hexdigest()[:16]
                    found.append(HockeyEvent(
                        id=uid, title=title, event_type=event_type,
                        rink=self.source["name"], city=self.source.get("city"),
                        state=self.source.get("state"), start=start, end=end,
                        register_url=register_url, source_url=url,
                        provider="sportified", last_updated=datetime.now(timezone.utc),
                    ))
        return found
