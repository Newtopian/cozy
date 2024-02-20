from datetime import datetime
from pathlib import Path
from typing import Generator

from cozy.model.models import Site, Chair, EventLog, ChairTakeEvent, ChairLeaveEvent, Staff, StaffAddEvent


class SiteController:

    def __init__(self, site_home: Path) -> None:
        self.home = site_home
        self.current_site_state = self.home / 'site_state.json'
        self.current_event_log_file = self.home / 'current_event_log.json'
        self.data_folder = self.home / 'data'
        self._site: Site | None = None
        self._active_staff: Staff | None = None

        if not self.home.exists():
            self.home.mkdir()

        if not self.data_folder.exists():
            self.data_folder.mkdir()

        if not self.current_site_state.exists():
            self._site = Site(capacity=25, name="Cozy", staff=[], chairs=[])
            self.save_site()
        else:
            self._site = Site.model_validate_json(self.current_site_state.read_text(encoding='utf-8'))

        if not self.current_event_log_file.exists():
            # finally we will start a new EventLog
            self.event_log = EventLog(initial_site_state=self._site.model_copy(deep=True), events=[])
        else:
            self.event_log = EventLog.model_validate_json(self.current_event_log_file.read_text(encoding='utf8'))

    @property
    def site(self) -> Site:
        return self._site

    def save_site(self):
        self.current_site_state.write_text(data=self.site.model_dump_json(indent=2), encoding='utf-8')
        if self.event_log:
            self.current_event_log_file.write_text(data=self.event_log.model_dump_json(indent=2), encoding='utf-8')

    def occupy_chair(self, chair: Chair):
        self.event_log.append(ChairTakeEvent(when=datetime.utcnow(), by=self.active_staff, chair=chair))
        self.save_site()

    def free_chair(self, chair: Chair):
        self.event_log.append(ChairLeaveEvent(when=datetime.utcnow(), by=self.active_staff, chair=chair))
        self.save_site()

    def add_staff(self, staff_name: str):
        if not self.site.has_staff(staff_name):
            staff = Staff(name=staff_name)
            self.site.staff.append(staff)
            self.event_log.append(StaffAddEvent(when=datetime.utcnow(), by=self.active_staff if self.active_staff else staff, who=staff))
            self.save_site()

    @property
    def active_staff(self) -> Staff | None:
        return self._active_staff

    @active_staff.setter
    def active_staff(self, staff: str | Staff) -> None:
        if staff is None:
            self._active_staff = None
            return
        if not isinstance(staff, Staff):
            staff = self.site.get_staff_from_name(staff)
        self._active_staff = staff


class Transaction:
    def __init__(self) -> None:
        pass

    def __enter__(self) -> 'Transaction':
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
