from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HockeyEvent(BaseModel):
    id: str
    title: str
    event_type: str
    rink: str
    city: Optional[str] = None
    state: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None
    register_url: Optional[str] = None
    source_url: Optional[str] = None
    provider: str
    last_updated: datetime

    # Optional availability metadata. Providers that do not expose these simply
    # leave them as None.
    capacity: Optional[int] = None
    registered_count: Optional[int] = None
    open_slots: Optional[int] = None
    registration_status: Optional[str] = None
