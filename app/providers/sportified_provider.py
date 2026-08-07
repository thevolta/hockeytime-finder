import re
from datetime import datetime, timedelta, timezone
from hashlib import sha1
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
    )
}

DATE_RE = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}\s+\d{4}$",
    re.I,
)
TIME_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*"
    r"(?P<end>\d{1,2}:\d{2}\s*(?:am|pm))",
    re.I,
)

EVENT_TYPES = {
    "Stick Time": ("stick time", "sticktime", "stick & puck", "stick and puck"),
    "Open Hockey": ("adult open hockey", "open hockey", "pickup hockey"),
    "Flow Hockey": ("flow hockey", "flow game"),
}


def _classify(text: str) -> Optional[str]:
    lowered = text.lower()
    for event_type, needles in EVENT_TYPES.items():
        if any(n in lowered for n in needles):
            return event_type
    return None


def _clean_title(text: str) -> str:
    text = TIME_RE.sub("", text)
    text = re.sub(r"\bRegister Online\b", "", text, flags=re.I)
    text = re.sub(
        r"\b(?:Mullett Arena|Mountain America Community Iceplex)\b",
        "",
        text,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", text).strip(" |-") or "Hockey Event"


def _location(text: str, default: str) -> str:
    if "Mountain America Community Iceplex" in text:
        return "Mountain America Community Iceplex"
    if "Mullett Arena" in text:
        return "Mullett Arena"
    return default


def _nearest_date(node: Tag) -> Optional[datetime.date]:
    for prev in node.find_all_previous(limit=80):
        text = " ".join(prev.stripped_strings)
        if DATE_RE.match(text):
            try:
                return datetime.strptime(text.replace(",", ""), "%A %B %d %Y").date()
            except ValueError:
                continue
    return None


def _registration_link(node: Tag, base_url: str) -> Optional[str]:
    # Try the event block itself, then a couple parent levels.
    candidates = [node]
    if node.parent and isinstance(node.parent, Tag):
        candidates.append(node.parent)
        if node.parent.parent and isinstance(node.parent.parent, Tag):
            candidates.append(node.parent.parent)

    for candidate in candidates:
        for a in candidate.find_all("a", href=True):
            label = " ".join(a.stripped_strings).lower()
            href = a.get("href", "")
            if "register" in label or "register" in href.lower():
                return urljoin(base_url, href)

    # If the event row itself is linked, that detail page is still preferable.
    for candidate in candidates:
        a = candidate.find("a", href=True)
        if a:
            return urljoin(base_url, a["href"])
    return None


class SportifiedProvider(BaseProvider):
    def fetch_events(self) -> List[HockeyEvent]:
        response = requests.get(
            self.source["url"], timeout=25, headers=HEADERS
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        events: list[HockeyEvent] = []
        seen: set[tuple] = set()

        # Find actual text nodes containing a time range. This is resilient to
        # Sportified changing table/div class names.
        for string_node in soup.find_all(string=TIME_RE):
            node = string_node.parent
            if not isinstance(node, Tag):
                continue

            # Walk upward until the block contains useful event context without
            # swallowing a large section of the page.
            block = node
            for _ in range(4):
                text = " ".join(block.stripped_strings)
                if _classify(text) and len(text) < 700:
                    break
                if not block.parent or not isinstance(block.parent, Tag):
                    break
                block = block.parent

            text = " ".join(block.stripped_strings)
            event_type = _classify(text)
            match = TIME_RE.search(text)
            if not event_type or not match:
                continue

            event_date = _nearest_date(block)
            if not event_date:
                continue

            start_time = datetime.strptime(
                match.group("start").lower().replace(" ", ""), "%I:%M%p"
            ).time()
            end_time = datetime.strptime(
                match.group("end").lower().replace(" ", ""), "%I:%M%p"
            ).time()

            start = datetime.combine(event_date, start_time, tzinfo=AZ_TZ)
            end = datetime.combine(event_date, end_time, tzinfo=AZ_TZ)
            if end <= start:
                end += timedelta(days=1)

            title = _clean_title(text)
            rink = _location(text, self.source["name"])
            register_url = _registration_link(block, self.source["url"])
            register_url = register_url or self.source.get("register_fallback")

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
                    register_url=register_url,
                    source_url=self.source["url"],
                    provider="sportified",
                    last_updated=datetime.now(timezone.utc),
                )
            )

        events.sort(key=lambda event: event.start)
        return events
