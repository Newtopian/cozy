from datetime import datetime
from enum import Enum
from typing import List

from pydantic.main import BaseModel


class Client(BaseModel):
    name: str

    def __str__(self):
        return self.name or ''


class Staff(BaseModel):
    name: str


class Chair(BaseModel):
    id: int
    occupant: Client | None
    since: datetime | None

    def __str__(self):
        return f"{self.occupant} @ {self.since.strftime('%A %H:%M')}" if self.occupant else "Empty"


class Site(BaseModel):
    capacity: int
    name: str
    staff: list[Staff]
    chairs: list[Chair]


class EventType(str, Enum):
    TAKE = "take",
    LEAVE = "leave",
    SWITCH = "switch"


class Event(BaseModel):
    type: EventType
    by: Staff
    at: datetime
    chair: Chair
    occupant: Client | None
    to_chair: Chair | None
