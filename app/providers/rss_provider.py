from datetime import datetime, timezone
from hashlib import sha1
from typing import List

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


KEYWORDS = {
    "Stick Time": ["stick time", "sticktime", "stick & puck", "stick and puck"],
    "Open Hockey": ["open hockey", "pickup hockey", "pick-up hockey"],
    "Flow Hockey": ["flow hockey", "flow game"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 HockeyTimeFinder/0.5",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def classify(text: str) -> str | None:
    lowered = text.lower()
    for event_type, terms in KEYWORDS.items():
        if any(term in lowered for term in terms):
            return event_type
    return None


class RSSProvider(BaseProvider):
    def fetch_events(self) -> List[HockeyEvent]:
        # Do not let feedparser perform an unbounded network request.
        response = requests.get(
            self.source["url"],
            timeout=int(self.source.get("request_timeout", 8)),
            headers=HEADERS,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        events: list[HockeyEvent] = []
        seen: set[str] = set()

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            plain_summary = BeautifulSoup(
                summary or "", "html.parser"
            ).get_text(" ", strip=True)

            event_type = classify(f"{title} {plain_summary}")
            if not event_type:
                continue

            raw_date = (
                getattr(entry, "start", None)
                or getattr(entry, "published", None)
                or getattr(entry, "updated", None)
                or title
            )

            try:
                start = dtparser.parse(str(raw_date), fuzzy=True)
            except Exception:
                continue

            link = getattr(entry, "link", None)
            uid_src = f'{self.source["name"]}|{title}|{start.isoformat()}'
            uid = sha1(uid_src.encode()).hexdigest()[:16]

            if uid in seen:
                continue
            seen.add(uid)

            events.append(
                HockeyEvent(
                    id=uid,
                    title=title,
                    event_type=event_type,
                    rink=self.source["name"],
                    city=self.source.get("city"),
                    state=self.source.get("state"),
                    start=start,
                    end=None,
                    register_url=link,
                    source_url=link or self.source["url"],
                    provider="rss",
                    last_updated=datetime.now(timezone.utc),
                )
            )

        events.sort(key=lambda event: event.start)
        return events
