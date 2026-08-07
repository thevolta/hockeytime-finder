from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
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
    """
    Pre-filter sources when a rink query is supplied.

    Examples:
      rink=AZ Ice            -> both AZ Ice sources
      rink=AZ Ice Arcadia    -> Arcadia only
      rink=Mullett           -> Mullett only
    """
    if not rink:
        return True

    query = rink.strip().lower()
    name = source.get("name", "").lower()

    return query in name or name in query


def _fetch_source(source: dict):
    provider_cls = PROVIDERS[source["provider"]]
    return provider_cls(source).fetch_events()


def fetch_all_events(
    rink: Optional[str] = None,
    source_timeout: int = 25,
):
    """
    Fetch sources concurrently so one slow/broken rink does not block all others.

    `rink` is applied before provider execution when possible, reducing unnecessary
    network requests for filtered API calls.
    """
    sources = [
        source
        for source in load_sources()
        if _matches_source(source, rink)
    ]

    events = []
    errors = []

    if not sources:
        return [], []

    # One worker per source is fine for this small provider set.
    max_workers = min(len(sources), 8)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_fetch_source, source): source
            for source in sources
        }

        for future in as_completed(future_map):
            source = future_map[future]
            try:
                result = future.result(timeout=source_timeout)
                events.extend(result)
            except TimeoutError:
                errors.append({
                    "source": source["name"],
                    "error": f"Timed out after {source_timeout} seconds",
                })
            except Exception as exc:
                errors.append({
                    "source": source["name"],
                    "error": str(exc),
                })

    events.sort(key=lambda e: e.start)
    return events, errors
