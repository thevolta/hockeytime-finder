from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import threading

from app.providers.daysmart_provider import DaySmartProvider
from app.providers.rss_provider import RSSProvider
from app.providers.sportified_provider import SportifiedProvider
from app.services.event_cache import (
    cache_count,
    get_meta,
    replace_source_events,
    set_meta,
)
from app.services.source_loader import load_sources


PROVIDERS = {
    "rss": RSSProvider,
    "sportified": SportifiedProvider,
    "daysmart": DaySmartProvider,
}

_REFRESH_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()
_REFRESHING = False

# Public/manual refresh protection.
MANUAL_COOLDOWN = timedelta(minutes=5)


def _set_refreshing(value: bool):
    global _REFRESHING
    with _STATE_LOCK:
        _REFRESHING = value


def is_refreshing() -> bool:
    with _STATE_LOCK:
        return _REFRESHING


def _fetch_one(source: dict):
    provider_cls = PROVIDERS[source["provider"]]
    events = provider_cls(source).fetch_events()
    return source, events


def refresh_cache(reason: str = "scheduled") -> dict:
    """
    Refresh all rink sources concurrently.

    Successful sources replace only their own cached rows. Failed sources retain
    their previous cached data, preventing temporary outages from blanking the
    public calendar.
    """
    if not _REFRESH_LOCK.acquire(blocking=False):
        return {
            "started": False,
            "reason": "refresh_already_running",
        }

    _set_refreshing(True)
    started = datetime.now(timezone.utc)
    set_meta("last_refresh_started", started.isoformat())
    set_meta("last_refresh_reason", reason)

    successes = {}
    errors = {}

    try:
        sources = load_sources()

        with ThreadPoolExecutor(max_workers=min(len(sources), 6)) as executor:
            future_map = {
                executor.submit(_fetch_one, source): source
                for source in sources
            }

            for future in as_completed(future_map):
                source = future_map[future]
                name = source["name"]

                try:
                    _, events = future.result()
                    replace_source_events(name, events)
                    successes[name] = len(events)
                except Exception as exc:
                    # Preserve the old source cache.
                    errors[name] = str(exc)

        finished = datetime.now(timezone.utc)

        result = {
            "started": True,
            "reason": reason,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "successes": successes,
            "errors": errors,
            "cached_event_count": cache_count(),
        }

        set_meta("last_refresh_finished", finished.isoformat())
        set_meta("last_refresh_result", result)

        if successes:
            set_meta("last_successful_refresh", finished.isoformat())

        return result

    finally:
        _set_refreshing(False)
        _REFRESH_LOCK.release()


def manual_refresh_allowed() -> tuple[bool, str | None]:
    if is_refreshing():
        return False, "A calendar refresh is already running."

    last_manual = get_meta("last_manual_refresh")
    if not last_manual:
        return True, None

    try:
        last_dt = datetime.fromisoformat(last_manual)
    except Exception:
        return True, None

    remaining = MANUAL_COOLDOWN - (datetime.now(timezone.utc) - last_dt)
    if remaining.total_seconds() > 0:
        minutes = max(1, int(remaining.total_seconds() // 60) + 1)
        return False, f"Manual refresh available again in about {minutes} minute(s)."

    return True, None


def mark_manual_refresh():
    set_meta("last_manual_refresh", datetime.now(timezone.utc).isoformat())
