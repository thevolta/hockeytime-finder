from typing import List
from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


class SportifiedProvider(BaseProvider):
    def fetch_events(self) -> List[HockeyEvent]:
        # TODO: move the tested Mullett/Sportified parser here.
        # This is intentionally scaffolded so provider logic stays isolated.
        return []
