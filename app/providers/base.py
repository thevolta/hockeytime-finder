from abc import ABC, abstractmethod
from typing import List
from app.models.event import HockeyEvent


class BaseProvider(ABC):
    def __init__(self, source: dict):
        self.source = source

    @abstractmethod
    def fetch_events(self) -> List[HockeyEvent]:
        raise NotImplementedError
