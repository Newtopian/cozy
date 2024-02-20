import math
from os.path import expanduser
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QScrollArea, QGridLayout, QInputDialog, QMessageBox, QTextEdit, QBoxLayout, QPlainTextEdit, QProgressBar
from datetime import datetime

from cozy.gemini_1 import StaffProgressWidget
from cozy.model.api import SiteController
from cozy.model.models import Chair, Client

site_api = SiteController(site_home=Path(expanduser("~")) / '.cozy_2')


class ChairWidget(QWidget):
    def __init__(self, chair: Chair):
        super().__init__()
        self._occupancy_button = None
        self.occupant_edit: QPlainTextEdit | None = None
        self._label = None
        self.chair = chair

        self.init_ui()

    def init_ui(self):
        layout = QBoxLayout(QBoxLayout.LeftToRight)

        self._label = QLabel(f"Chair {self.chair.id:>3}")
        layout.addWidget(self._label)

        self.occupant_edit = QPlainTextEdit("", self)
        self.occupant_edit.textChanged.connect(self.editing_ocupy)
        self.occupant_edit.setMaximumHeight(20)
        self.occupant_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.occupant_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout.addWidget(self.occupant_edit)

        self._occupancy_button = QPushButton("Take", self)
        self._occupancy_button.clicked.connect(self.toggle_occupancy)
        layout.addWidget(self._occupancy_button)

        self.setLayout(layout)

    def editing_ocupy(self):
        if self.chair.occupant is not None:
            self.chair.occupant.name = self.occupant_edit.toPlainText().strip()

    def occupy(self):
        if self.occupant_edit.toPlainText().strip() != "":
            self.chair.occupant = Client(name=self.occupant_edit.toPlainText().strip())
            self.chair.since = datetime.now()
            self._occupancy_button.setText(f"{self.chair.since:'%A %H:%M'} -- Click to free")

    def release(self):
        self.chair.occupant = None
        self.chair.since = None
        self.occupant_edit.setPlainText('')
        self._occupancy_button.setText(f"Take")

    def toggle_occupancy(self):
        if self.chair.is_occupied:
            self.release()
            site_api.free_chair(self.chair)
        else:
            self.occupy()
            site_api.occupy_chair(self.chair)

    @property
    def occupied(self) -> bool:
        return self.chair.occupant is not None


class ChairTrackingUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self._chair_widgets = {}
        self.staff_section = None
        self.init_ui()

    def staff_added_handler(self, staff_name: str) -> None:
        site_api.add_staff(staff_name)

    def staff_selected_handler(self, staff_name: str) -> None:
        site_api.active_staff = staff_name

    def staff_selected_cleared_handler(self) -> None:
        site_api.active_staff = None

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.staff_section = StaffProgressWidget()
        self.staff_section.staff_added.connect(self.staff_added_handler)
        self.staff_section.staff_selected.connect(self.staff_selected_handler)
        self.staff_section.staff_selection_cleared.connect(self.staff_selected_cleared_handler)

        # and finally we add any currently known staff members
        for s in site_api.site.staff:
            self.staff_section.add_staff(s.name)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.staff_section)
        central_widget_layout.addWidget(scroll_area)

        scroll_content = QWidget(self)
        scroll_area.setWidget(scroll_content)

        grid_layout = QGridLayout(scroll_content)

        for c in site_api.site.chairs:
            row = math.ceil(c.id / 2)
            col = (c.id - 1) % 2
            chair_widget = ChairWidget(c)
            grid_layout.addWidget(chair_widget, row, col)
            self._chair_widgets[c.id] = chair_widget

        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle('Chair Tracking System')
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    window = ChairTrackingUI()
    app.exec()
