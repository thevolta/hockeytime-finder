from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


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
