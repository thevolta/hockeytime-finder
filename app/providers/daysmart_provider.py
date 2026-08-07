from typing import List
from app.models.event import HockeyEvent
from app.providers.base import BaseProvider


class DaySmartProvider(BaseProvider):
    def fetch_events(self) -> List[HockeyEvent]:
        # TODO: identify the DaySmart schedule endpoint used by AZ Ice.
        # Registration fallback is already stored in sources.yaml.
        return []
