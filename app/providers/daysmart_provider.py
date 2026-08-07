import re
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from typing import List, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from app.models.event import HockeyEvent
from app.providers.base import BaseProvider

AZ_TZ = ZoneInfo("America/Phoenix")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    )
}

EVENT_TYPES = {
    "Stick Time": ("stick time", "sticktime", "stick and puck", "stick & puck"),
    "Open Hockey": ("pickup hockey", "open hockey", "adult open hockey"),
}

# Handles text such as:
# Aug 8th Sat 1:00 pm 1h 30m Stick Time AZ Ice Arcadia
DATE_TIME_RE = re.compile(
    r"(?P<month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?"
    r".{0,40}?"
    r"(?P<time>\d{1,2}:\d{2}\s*(?:am|pm))",
    re.I | re.S,
)
DURATION_RE = re.compile(r"\b(?:(?P<hours>\d+)\s*h)?\s*(?:(?P<mins>\d+)\s*m)?\b", re.I)


def _classify(text: str) -> Optional[str]:
    lowered = text.lower()
    for event_type, needles in EVENT_TYPES.items():
        if any(n in lowered for n in needles):
            return event_type
    return None


def _candidate_year(month: int) -> int:
    now = datetime.now(AZ_TZ)
    # DaySmart's legacy schedule pages often omit year. Pick the nearest
    # reasonable occurrence, rolling into next year for old months.
    year = now.year
    candidate = datetime(year, month, 1, tzinfo=AZ_TZ)
    if candidate < now - timedelta(days=120):
        year += 1
    return year


class DaySmartProvider(BaseProvider):
    def _get(self, url: str) -> requests.Response:
        response = requests.get(url, timeout=25, headers=HEADERS)
        response.raise_for_status()
        return response

    def discover_calendar_url(self) -> Optional[str]:
        response = self._get(self.source["url"])
        soup = BeautifulSoup(response.text, "html.parser")

        for iframe in soup.find_all("iframe", src=True):
            src = urljoin(response.url, iframe["src"])
            if "daysmartrecreation.com" in src.lower():
                return src

        # Some pages put it in a data-src for lazy loading.
        for iframe in soup.find_all("iframe"):
            src = iframe.get("data-src")
            if src and "daysmartrecreation.com" in src.lower():
                return urljoin(response.url, src)

        return self.source.get("calendar_url")

    def diagnostic(self) -> dict:
        calendar_url = self.discover_calendar_url()
        result = {
            "source": self.source["name"],
            "public_page": self.source["url"],
            "calendar_url": calendar_url,
            "register_fallback": self.source.get("register_fallback"),
            "calendar_fetch_ok": False,
            "calendar_title": None,
            "calendar_text_sample": None,
        }

        if not calendar_url:
            return result

        try:
            response = self._get(calendar_url)
            soup = BeautifulSoup(response.text, "html.parser")
            result["calendar_fetch_ok"] = True
            result["calendar_title"] = (
                soup.title.get_text(" ", strip=True) if soup.title else None
            )
            text = " ".join(soup.stripped_strings)
            result["calendar_text_sample"] = text[:1200]
        except Exception as exc:
            result["calendar_error"] = str(exc)

        return result

    def fetch_events(self) -> List[HockeyEvent]:
        calendar_url = self.discover_calendar_url()
        if not calendar_url:
            return []

        response = self._get(calendar_url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(soup.stripped_strings)

        events: list[HockeyEvent] = []
        seen: set[tuple] = set()

        # Split into modest chunks so one keyword doesn't claim the whole page.
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            event_type = _classify(line)
            if not event_type:
                continue

            context = " ".join(lines[max(0, index - 6): index + 7])
            date_match = DATE_TIME_RE.search(context)
            if not date_match:
                continue

            month = datetime.strptime(date_match.group("month")[:3], "%b").month
            year = _candidate_year(month)
            day = int(date_match.group("day"))
            event_time = datetime.strptime(
                date_match.group("time").lower().replace(" ", ""), "%I:%M%p"
            ).time()
            start = datetime(year, month, day, event_time.hour, event_time.minute, tzinfo=AZ_TZ)

            end = None
            duration_match = re.search(
                r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?",
                context,
                re.I,
            )
            if duration_match and (duration_match.group(1) or duration_match.group(2)):
                hours = int(duration_match.group(1) or 0)
                minutes = int(duration_match.group(2) or 0)
                if hours or minutes:
                    end = start + timedelta(hours=hours, minutes=minutes)

            title = line
            rink = self.source["name"]
            if "AZ Ice Arcadia" in context:
                rink = "AZ Ice Arcadia"
            elif "AZ Ice Peoria" in context:
                rink = "AZ Ice Peoria"

            key = (title.lower(), start.isoformat(), rink.lower())
            if key in seen:
                continue
            seen.add(key)

            uid_src = f"{rink}|{title}|{start.isoformat()}"
            uid = sha1(uid_src.encode()).hexdigest()[:16]

            events.append(
                HockeyEvent(
                    id=uid,
                    title=title,
                    event_type=event_type,
                    rink=rink,
                    city=self.source.get("city"),
                    state=self.source.get("state"),
                    start=start,
                    end=end,
                    register_url=self.source.get("register_fallback"),
                    source_url=calendar_url,
                    provider="daysmart",
                    last_updated=datetime.now(timezone.utc),
                )
            )

        events.sort(key=lambda event: event.start)
        return events
