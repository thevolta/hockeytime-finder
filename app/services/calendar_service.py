from icalendar import Calendar, Event as ICalEvent
from app.models.event import HockeyEvent


def build_ics(events: list[HockeyEvent]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//HockeyTime Finder//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "HockeyTime Finder")

    for event in events:
        item = ICalEvent()
        item.add("uid", f"{event.id}@hockeytime-finder")
        item.add("summary", f"{event.event_type} - {event.rink}")
        item.add("dtstart", event.start)
        if event.end:
            item.add("dtend", event.end)

        description = [event.title]
        if event.register_url:
            description.append(f"Register: {event.register_url}")
            item.add("url", event.register_url)
        elif event.source_url:
            item.add("url", event.source_url)

        item.add("description", "\n".join(description))
        location = ", ".join(
            part for part in [event.rink, event.city, event.state] if part
        )
        item.add("location", location)
        cal.add_component(item)

    return cal.to_ical()
