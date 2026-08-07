from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response

from app.providers.daysmart_provider import DaySmartProvider
from app.services.calendar_service import build_ics
from app.services.event_cache import (
    cache_count,
    get_cached_events,
    get_meta,
    source_counts,
)
from app.services.refresh_service import (
    is_refreshing,
    manual_refresh_allowed,
    mark_manual_refresh,
    refresh_cache,
)
from app.services.source_loader import load_sources


router = APIRouter()


def _filtered_cached_events(
    state: str | None = None,
    rink: str | None = None,
    event_type: str | None = None,
):
    events = get_cached_events()
    now = datetime.now(timezone.utc)

    # Remove events that are clearly in the past from public responses.
    events = [
        event for event in events
        if event.end is None or event.end.astimezone(timezone.utc) >= now
    ]

    if state:
        events = [
            event for event in events
            if (event.state or "").lower() == state.lower()
        ]

    if rink:
        events = [
            event for event in events
            if rink.lower() in event.rink.lower()
        ]

    if event_type:
        events = [
            event for event in events
            if event_type.lower() in event.event_type.lower()
        ]

    return events


@router.get("/api/events")
def get_events(
    state: str | None = Query(default=None),
    rink: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
):
    # Production API reads ONLY from cache. No rink site requests happen here.
    return {
        "events": _filtered_cached_events(state, rink, event_type),
        "cache": {
            "refreshing": is_refreshing(),
            "last_successful_refresh": get_meta("last_successful_refresh"),
            "last_refresh_result": get_meta("last_refresh_result"),
        },
    }


@router.post("/api/refresh", status_code=202)
def manual_refresh(background_tasks: BackgroundTasks):
    allowed, message = manual_refresh_allowed()
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    mark_manual_refresh()
    background_tasks.add_task(refresh_cache, "manual")

    return {
        "accepted": True,
        "message": "Calendar refresh started.",
    }


@router.get("/api/status")
def provider_status():
    return {
        "cached_event_count": cache_count(),
        "sources": source_counts(),
        "refreshing": is_refreshing(),
        "last_successful_refresh": get_meta("last_successful_refresh"),
        "last_refresh_started": get_meta("last_refresh_started"),
        "last_refresh_finished": get_meta("last_refresh_finished"),
        "last_refresh_result": get_meta("last_refresh_result"),
    }


@router.get("/api/diagnostics/daysmart")
def daysmart_diagnostics():
    results = []
    for source in load_sources():
        if source.get("provider") == "daysmart":
            try:
                results.append(DaySmartProvider(source).diagnostic())
            except Exception as exc:
                results.append(
                    {"source": source.get("name"), "error": str(exc)}
                )
    return {"daysmart": results}


@router.get("/calendar.ics")
def calendar_feed():
    data = build_ics(_filtered_cached_events())
    return Response(
        content=data,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'inline; filename="hockeytime-finder.ics"'
        },
    )
