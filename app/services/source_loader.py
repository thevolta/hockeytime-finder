from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import Optional

import yaml

from app.providers.rss_provider import RSSProvider
from app.providers.sportified_provider import SportifiedProvider
from app.providers.daysmart_provider import DaySmartProvider


PROVIDERS = {
    "rss": RSSProvider,
    "sportified": SportifiedProvider,
    "daysmart": DaySmartProvider,
}


def load_sources() -> list[dict]:
    path = Path(__file__).resolve().parents[1] / "config" / "sources.yaml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _matches_source(source: dict, rink: Optional[str]) -> bool:
    if not rink:
        return True
    query = rink.strip().lower()
    name = source.get("name", "").lower()
    return query in name or name in query


def _fetch_source(source: dict):
    provider_cls = PROVIDERS[source["provider"]]
    return provider_cls(source).fetch_events()


def _dedupe_events(events):
    unique = {}
    for event in events:
        # Stable cross-provider final de-dupe.
        key = (
            event.provider,
            event.rink.lower(),
            event.event_type.lower(),
            event.start.isoformat(),
        )
        unique[key] = event
    return list(unique.values())


def fetch_all_events(
    rink: Optional[str] = None,
    source_timeout: int = 18,
):
    sources = [
        source for source in load_sources()
        if _matches_source(source, rink)
    ]

    if not sources:
        return [], []

    events = []
    errors = []

    executor = ThreadPoolExecutor(max_workers=min(len(sources), 8))
    future_map = {
        executor.submit(_fetch_source, source): source
        for source in sources
    }

    done, not_done = wait(future_map.keys(), timeout=source_timeout)

    for future in done:
        source = future_map[future]
        try:
            events.extend(future.result())
        except Exception as exc:
            errors.append({
                "source": source["name"],
                "error": str(exc),
            })

    for future in not_done:
        source = future_map[future]
        future.cancel()
        errors.append({
            "source": source["name"],
            "error": f"Provider exceeded {source_timeout}-second response budget",
        })

    executor.shutdown(wait=False, cancel_futures=True)

    events = _dedupe_events(events)
    events.sort(key=lambda e: e.start)
    return events, errors
