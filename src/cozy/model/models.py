import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, date

from typing import List, Any
from pydantic import Field, SerializeAsAny
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

    def take(self, client: Client, since: datetime | None = None) -> None:
        if self.occupant:
            raise DoubleOccupancyError(self, client)
        self.occupant = client
        self.since = since if since is not None else datetime.now()

    @property
    def is_occupied(self) -> bool:
        return self.occupant is not None

    def __str__(self):
        return f"{self.occupant} @ {self.since.strftime('%A %H:%M')}" if self.occupant else "Empty"


class Site(BaseModel):
    capacity: int
    name: str
    staff: list[Staff]
    chairs: list[Chair]

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self._capacity = 0
        self.init_chairs(data['capacity'] if 'capacity' in data else 0)

    @property
    def capacity(self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        if self._capacity != value:
            self.init_chairs(value)

    @property
    def busy_count(self):
        return len([c for c in self.chairs if c.is_occupied])

    def occupy(self, chair_id: int, client: Client, since: datetime | None) -> None:
        self.chairs[chair_id].take(client, since)

    def init_chairs(self, target_capacity: int) -> None:
        # so adding capacity is simple...
        while len(self.chairs) < target_capacity:
            self.chairs.append(Chair(id=len(self.chairs) + 1, occupant=None, since=None))
        # but removing capacity...  we must "move" people in the slice of chairs
        # into a free chair of the kept capacity
        if self.busy_count > target_capacity:
            raise SiteResizeBelowOccupancyException(self, target_capacity)
        to_be_relocated = self.chairs[target_capacity:]
        to_be_kept = self.chairs[:target_capacity]
        # go through the chairs to be removed and move them such that their relative ordering in chairs remains the same
        for chair in reversed(to_be_relocated):
            for c in reversed(to_be_kept):
                if not c.is_occupied:
                    c.take(chair.occupant, since=chair.since)
        self._capacity = target_capacity

    def has_staff(self, name: str) -> bool:
        return name in [s.name for s in self.staff]

    def get_staff_from_name(self, name: str) -> Staff:
        if self.has_staff(name):
            return [s for s in self.staff if s.name == name].pop()

        raise StaffNotFoundError(name)


class SiteException(Exception):
    pass


class SiteResizeBelowOccupancyException(SiteException):
    def __init__(self, site: Site, desired_capacity) -> None:
        super().__init__(f"Site resize requested [from {site.capacity} to {desired_capacity}] but current occupancy rate [total {site.busy_count} chairs] is higher than desired chair count, please set new occupancy higher or free some chairs")
        self.site = site
        self.desired_capacity = desired_capacity


class DoubleOccupancyError(SiteException):
    def __init__(self, chair: Chair, client: Client) -> None:
        super().__init__(f"This chair [{chair.id}] is already occupied by [{chair.occupant}], please choose another chair for [{client}]")


class StaffNotFoundError(SiteException):
    def __init__(self, staff_name: str):
        super().__init__(f"Could not find this staff [{staff_name}] within registered staff members")


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    when: datetime
    by: Staff


class SiteResizedEvent(Event):
    capacity: int


class ChairTakeEvent(Event):
    chair: Chair


class ChairLeaveEvent(Event):
    chair: Chair


class StaffAddEvent(Event):
    who: Staff


class StaffRemoveEvent(Event):
    who: Staff


class ClientAddEvent(Event):
    who: Client


class ClientRemoveEvent(Event):
    who: Client


class EventLog(BaseModel):
    initial_site_state: Site | None
    event_order: List[UUID] = Field(default_factory=list)
    site_resize_events: List[SiteResizedEvent] = Field(default_factory=list)
    chair_take_events: List[ChairTakeEvent] = Field(default_factory=list)
    chair_leave_events: List[ChairLeaveEvent] = Field(default_factory=list)
    staff_add_events: List[StaffAddEvent] = Field(default_factory=list)
    staff_remove_events: List[StaffRemoveEvent] = Field(default_factory=list)
    client_add_events: List[ClientAddEvent] = Field(default_factory=list)
    client_remove_events: List[ClientRemoveEvent] = Field(default_factory=list)
    final_site_state: Site | None = None

    def append(self, event: Event) -> None:
        self.event_order.append(event.id)

        if isinstance(event, SiteResizedEvent):
            self.site_resize_events.append(event)
        elif isinstance(event, ChairTakeEvent):
            self.chair_take_events.append(event)
        elif isinstance(event, ChairLeaveEvent):
            self.chair_leave_events.append(event)
        elif isinstance(event, StaffAddEvent):
            self.staff_add_events.append(event)
        elif isinstance(event, StaffRemoveEvent):
            self.staff_remove_events.append(event)
        elif isinstance(event, ClientAddEvent):
            self.client_add_events.append(event)
        elif isinstance(event, ClientRemoveEvent):
            self.client_remove_events.append(event)
        else:
            raise ValueError("Unknown Event")

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)

# Save EventLog instance to a file
def save_event_log(event_log: EventLog, file_path: Path):
    with open(file_path, 'w') as file:
        file.write(event_log.model_dump_json())
        #json.dump(event_log.dict(), file,  cls=UUIDEncoder)



# Load EventLog instance from a file
def load_event_log(file_path: Path) -> EventLog:
    with open(file_path, 'r') as file:
        data = json.load(file)
        return EventLog(**data)

# Example usage
if __name__ == "__main__":
    # Creating an instance of EventLog
    event_log_instance = EventLog(
        initial_site_state=None,
        final_site_state=None
    )
    event_log_instance.append(ChairTakeEvent(when=datetime.utcnow(), by=Staff(name="John"), chair=Chair(occupant=Client(name="Chair1"), since=datetime.utcnow(), id=1)))
    event_log_instance.append(StaffAddEvent(when=datetime.utcnow(), by=Staff(name="Admin"), who=Staff(name="Staff1")))


    # Save the instance to a file
    save_event_log(event_log_instance, Path("event_log.json"))

    # Load the instance from a file
    loaded_event_log_instance = load_event_log(Path("event_log.json"))

    # Verify the loaded instance
    print(loaded_event_log_instance)
