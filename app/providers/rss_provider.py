from datetime import datetime, timezone
from hashlib import sha1
from typing import List

import feedparser
from dateutil import parser as dtparser

from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


KEYWORDS = {
    "Stick Time": ["stick time", "sticktime", "stick & puck", "stick and puck"],
    "Open Hockey": ["open hockey", "pickup hockey", "pick-up hockey"],
    "Flow Hockey": ["flow hockey", "flow game"],
}


def classify(text: str) -> str | None:
    lowered = text.lower()
    for event_type, terms in KEYWORDS.items():
        if any(term in lowered for term in terms):
            return event_type
    return None


class RSSProvider(BaseProvider):
    def fetch_events(self) -> List[HockeyEvent]:
        feed = feedparser.parse(self.source["url"])
        events: list[HockeyEvent] = []

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            event_type = classify(f"{title} {summary}")
            if not event_type:
                continue

            raw_date = (
                getattr(entry, "start", None)
                or getattr(entry, "published", None)
                or getattr(entry, "updated", None)
            )
            if not raw_date:
                continue

            try:
                start = dtparser.parse(str(raw_date))
            except Exception:
                continue

            link = getattr(entry, "link", None)
            uid_src = f'{self.source["name"]}|{title}|{start.isoformat()}'
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
                    end=None,
                    register_url=link,
                    source_url=link or self.source["url"],
                    provider="rss",
                    last_updated=datetime.now(timezone.utc),
                )
            )

        return events
