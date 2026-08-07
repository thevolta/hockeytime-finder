from pathlib import Path
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


def fetch_all_events():
    events = []
    errors = []

    for source in load_sources():
        provider_cls = PROVIDERS[source["provider"]]
        try:
            events.extend(provider_cls(source).fetch_events())
        except Exception as exc:
            errors.append({"source": source["name"], "error": str(exc)})

    events.sort(key=lambda e: e.start)
    return events, errors
