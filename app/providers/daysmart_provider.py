from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
import re
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
from dateutil import parser as dtparser

from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


API_URL = "https://api.daysmartrecreation.com/v1/events"
AZ_TZ = ZoneInfo("America/Phoenix")

HEADERS = {
    "Accept": "application/vnd.api+json",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://apps.daysmartrecreation.com",
    "Referer": "https://apps.daysmartrecreation.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    ),
}

EVENT_KEYWORDS = {
    "Stick Time": (
        "stick time",
        "sticktime",
        "stick & puck",
        "stick and puck",
    ),
    "Open Hockey": (
        "pick up hockey",
        "pickup hockey",
        "pick-up hockey",
        "open hockey",
        "adult open hockey",
    ),
}


def _strip_html(value: Optional[str]) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", unescape(value))
    return re.sub(r"\s+", " ", text).strip()


def _classify(*values: Optional[str]) -> Optional[str]:
    text = " ".join(v or "" for v in values).lower()
    for event_type, needles in EVENT_KEYWORDS.items():
        if any(needle in text for needle in needles):
            return event_type
    return None


def _index_included(items: list[dict]) -> Dict[Tuple[str, str], dict]:
    return {
        (str(item.get("type")), str(item.get("id"))): item
        for item in items
        if item.get("type") is not None and item.get("id") is not None
    }


def _relationship_id(item: dict, relationship: str) -> Optional[Tuple[str, str]]:
    data = (
        item.get("relationships", {})
        .get(relationship, {})
        .get("data")
    )
    if isinstance(data, dict) and data.get("type") and data.get("id") is not None:
        return str(data["type"]), str(data["id"])
    return None


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    dt = dtparser.isoparse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AZ_TZ)
    return dt.astimezone(AZ_TZ)


class DaySmartProvider(BaseProvider):
    """
    Lightweight direct DaySmart JSON:API provider.

    The previous version requested a 30-day company-wide payload in one shot.
    This version:
      - requests only the relationships we actually use
      - splits the 30-day window into 3-day chunks
      - fetches chunks concurrently
      - still filters by configured facility ID locally
    """

    def __init__(self, source: dict):
        super().__init__(source)

    def _base_params(self, start: datetime, end: datetime) -> dict:
        return {
            "cache[save]": "false",
            "page[size]": 100,
            "page[number]": 1,
            "sort": "start",
            "company": self.source.get("company", "azice"),
            "filter[start__gte]": start.strftime("%Y-%m-%d %H:%M:%S"),
            "filter[start__lte]": end.strftime("%Y-%m-%d %H:%M:%S"),
            "filter[resource.facility.my_sam_visible]": "true",
            "filter[eventType.code__not]": "L",
            "include": "summary,resource.facility",
        }

    def _fetch_chunk(self, start: datetime, end: datetime) -> list[dict]:
        session = requests.Session()
        session.headers.update(HEADERS)

        pages: list[dict] = []
        params = self._base_params(start, end)
        page_number = 1

        while True:
            params["page[number]"] = page_number
            response = session.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            pages.append(payload)

            meta = payload.get("meta", {}).get("page", {})
            last_page = int(meta.get("last-page") or meta.get("last_page") or 1)

            if page_number >= last_page:
                break

            page_number += 1
            if page_number > 20:
                break

        return pages

    def _chunks(self, start: datetime, end: datetime):
        chunk_days = int(self.source.get("chunk_days", 3))
        current = start

        while current <= end:
            chunk_end = min(
                current + timedelta(days=chunk_days) - timedelta(seconds=1),
                end,
            )
            yield current, chunk_end
            current = chunk_end + timedelta(seconds=1)

    def _event_from_json(
        self,
        item: dict,
        included: Dict[Tuple[str, str], dict],
    ) -> Optional[HockeyEvent]:
        attrs = item.get("attributes", {})

        resource_ref = _relationship_id(item, "resource")
        resource = included.get(resource_ref, {}) if resource_ref else {}
        resource_attrs = resource.get("attributes", {})

        facility_ref = _relationship_id(resource, "facility") if resource else None
        facility = included.get(facility_ref, {}) if facility_ref else {}
        facility_attrs = facility.get("attributes", {})

        expected_facility_id = self.source.get("facility_id")
        actual_facility_id = (
            str(facility.get("id"))
            if facility.get("id") is not None
            else str(resource_attrs.get("facility_id") or "")
        )

        if expected_facility_id is not None and actual_facility_id != str(expected_facility_id):
            return None

        summary_ref = _relationship_id(item, "summary")
        summary = included.get(summary_ref, {}) if summary_ref else {}
        summary_attrs = summary.get("attributes", {})

        title = (
            summary_attrs.get("name")
            or attrs.get("desc")
            or "Hockey Event"
        )

        description = _strip_html(
            attrs.get("best_description")
            or attrs.get("description")
        )

        event_type = _classify(
            title,
            description,
            attrs.get("desc"),
            summary_attrs.get("event_type"),
        )
        if not event_type:
            return None

        start = _parse_dt(summary_attrs.get("start_date") or attrs.get("start"))
        end = _parse_dt(summary_attrs.get("end_date") or attrs.get("end"))
        if not start:
            return None

        rink = facility_attrs.get("name") or self.source["name"]

        capacity = attrs.get("register_capacity")
        registered_count = summary_attrs.get("registered_count")
        open_slots = summary_attrs.get("open_slots")
        registration_status = summary_attrs.get("registration_status")

        if isinstance(open_slots, int) and open_slots < 0:
            open_slots = None
        if isinstance(capacity, int) and capacity <= 0:
            capacity = None

        event_id = str(item.get("id"))

        return HockeyEvent(
            id=f"daysmart-{self.source.get('company', 'azice')}-{event_id}",
            title=title,
            event_type=event_type,
            rink=rink,
            city=self.source.get("city"),
            state=self.source.get("state"),
            start=start,
            end=end,
            register_url=self.source.get("register_fallback"),
            source_url=f"{API_URL}/{event_id}",
            provider="daysmart",
            last_updated=datetime.now(timezone.utc),
            capacity=capacity,
            registered_count=registered_count,
            open_slots=open_slots,
            registration_status=registration_status,
        )

    def fetch_events(self) -> List[HockeyEvent]:
        now = datetime.now(AZ_TZ)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(
            days=int(self.source.get("days_ahead", 30)),
            hours=23,
            minutes=59,
            seconds=59,
        )

        chunks = list(self._chunks(start, end))
        pages: list[dict] = []

        max_workers = min(int(self.source.get("chunk_workers", 5)), len(chunks))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._fetch_chunk, chunk_start, chunk_end): (chunk_start, chunk_end)
                for chunk_start, chunk_end in chunks
            }

            for future in as_completed(futures):
                pages.extend(future.result())

        events: list[HockeyEvent] = []
        seen: set[str] = set()

        for payload in pages:
            included = _index_included(payload.get("included", []))

            for item in payload.get("data", []):
                event = self._event_from_json(item, included)
                if not event or event.id in seen:
                    continue
                seen.add(event.id)
                events.append(event)

        events.sort(key=lambda event: event.start)
        return events

    def diagnostic(self) -> dict:
        now = datetime.now(AZ_TZ)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(seconds=1)

        try:
            pages = self._fetch_chunk(start, end)
            total = sum(len(page.get("data", [])) for page in pages)
            matching = 0

            for payload in pages:
                included = _index_included(payload.get("included", []))
                for item in payload.get("data", []):
                    if self._event_from_json(item, included):
                        matching += 1

            return {
                "source": self.source["name"],
                "provider": "daysmart-api",
                "facility_id": self.source.get("facility_id"),
                "api_fetch_ok": True,
                "raw_events_in_window": total,
                "matching_hockey_events": matching,
            }
        except Exception as exc:
            return {
                "source": self.source["name"],
                "provider": "daysmart-api",
                "facility_id": self.source.get("facility_id"),
                "api_fetch_ok": False,
                "error": str(exc),
            }
