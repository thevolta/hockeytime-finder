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
    events, errors = fetch_all_events()

    if state:
        events = [e for e in events if (e.state or "").lower() == state.lower()]
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
