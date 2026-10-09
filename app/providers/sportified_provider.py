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
        events.sort(key=lambda event: event.start)
        return events

    def _fetch_schedule_skills(self, now, seen):
        """Read the public schedule's rolling seven-day windows."""
        found = []
        # Sportified accepts ?date=YYYY-MM-DD to move its seven-day window.
        for offset in (0, 7, 14, 21, 28):
            date = (now + timedelta(days=offset)).date().isoformat()
            url = f"https://mullett.sportified.net/schedule?date={date}"
            soup = self._fetch_page(url)
            # Schedule displays day headings and event lines in chronological order.
            # Parse visible text, which also covers its mobile duplicate layout.
            lines = [re.sub(r"\\s+", " ", t).strip()
                     for t in soup.get_text("\\n").splitlines()]
            lines = [line for line in lines if line]
            current_date = None
            heading = re.compile(
                r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), "
                r"([A-Za-z]+ \\d{1,2} \\d{4})$")
            times = re.compile(
                r"^(\\d{1,2}:\\d{2}\\s*[ap]m)\\s*-\\s*"
                r"(\\d{1,2}:\\d{2}\\s*[ap]m)$", re.I)
            for i, line in enumerate(lines):
                match_day = heading.match(line)
                if match_day:
                    current_date = datetime.strptime(match_day.group(1), "%B %d %Y").date()
                    continue
                tm = times.match(line)
                if not tm or current_date is None:
                    continue
                # The schedule's table is time | title | rink.
                # Ignore duplicate mobile rows, where title precedes time.
                title = lines[i+1] if i+1 < len(lines) else ""
                if "adult rookie class" not in title.lower() and "adult skills" not in title.lower():
                    continue
                start_t = datetime.strptime(tm.group(1).replace(" ", "").lower(), "%I:%M%p").time()
                end_t = datetime.strptime(tm.group(2).replace(" ", "").lower(), "%I:%M%p").time()
                start = datetime.combine(current_date, start_t, tzinfo=AZ_TZ)
                end = datetime.combine(current_date, end_t, tzinfo=AZ_TZ)
                if end <= start:
                    end += timedelta(days=1)
                if end < now - timedelta(hours=2):
                    continue
                event_type = "Adult Skills"
                key = (event_type, start.isoformat(), end.isoformat())
                if key in seen:
                    continue
                seen.add(key)
                uid = sha1(f"{self.source['name']}|{event_type}|{start.isoformat()}".encode()).hexdigest()[:16]
                found.append(HockeyEvent(
                    id=uid, title=title, event_type=event_type,
                    rink=self.source["name"], city=self.source.get("city"),
                    state=self.source.get("state"), start=start, end=end,
                    register_url="https://mullett.sportified.net/products/24226",
                    source_url=url, provider="sportified",
                    last_updated=datetime.now(timezone.utc),
                ))
        return found
