from fastapi import APIRouter, Query, Response
from app.services.source_loader import fetch_all_events, load_sources
from app.services.calendar_service import build_ics
from app.providers.daysmart_provider import DaySmartProvider

router = APIRouter()


@router.get("/api/events")
def get_events(
    state: str | None = Query(default=None),
    rink: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
):
    # Pass rink through so providers can be pre-filtered before network calls.
    events, errors = fetch_all_events(rink=rink)

    if state:
        events = [e for e in events if (e.state or "").lower() == state.lower()]

    # Keep the event-level filter too, since provider/source names and final rink
    # names are not always identical.
    if rink:
        events = [e for e in events if rink.lower() in e.rink.lower()]

    if event_type:
        events = [
            e for e in events if event_type.lower() in e.event_type.lower()
        ]

    return {"events": events, "errors": errors}


@router.get("/api/diagnostics/daysmart")
def daysmart_diagnostics():
    results = []
    for source in load_sources():
        if source.get("provider") == "daysmart":
            try:
                results.append(DaySmartProvider(source).diagnostic())
            except Exception as exc:
                results.append(
                    {
                        "source": source.get("name"),
                        "error": str(exc),
                    }
                )
    return {"daysmart": results}


@router.get("/api/status")
def provider_status():
    """
    Quick source health view. Useful when the UI says Loading or reports errors.
    """
    events, errors = fetch_all_events(source_timeout=20)

    counts = {}
    for event in events:
        counts[event.rink] = counts.get(event.rink, 0) + 1

    return {
        "event_count": len(events),
        "rinks": counts,
        "errors": errors,
    }


@router.get("/calendar.ics")
def calendar_feed():
    events, _ = fetch_all_events()
    data = build_ics(events)
    return Response(
        content=data,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'inline; filename="hockeytime-finder.ics"'
        },
    )
