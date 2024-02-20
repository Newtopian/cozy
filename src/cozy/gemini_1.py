import sys
from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QLineEdit,
    QFontDialog
)


class StaffProgressWidget(QWidget):
    staff_added = Signal(str)
    staff_selected = Signal(str)
    staff_selection_cleared = Signal()

    timer_granularity_steps_per_seconds: int
    active_time_seconds: int

    def __init__(self, parent=None):
        super().__init__(parent)
        self.staff_name_input = None
        self.add_staff_button = None
        self.staff_buttons_layout = None
        self.progress_label = None
        self.progress_bar = None
        self.staff_buttons = {}
        self.current_staff = None
        self.timer = None
        self.active_time_seconds = 10
        self.timer_granularity_steps_per_seconds = 100

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Staff Progress")

        # Progress bar (initially disabled)
        self.progress_bar: QProgressBar = QProgressBar(self)
        self.progress_bar.setEnabled(False)
        self.progress_bar.setMaximum(self.timer_granularity_steps_per_seconds * self.active_time_seconds)  # 10-second progress
        self.progress_bar.setMinimum(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setTextVisible(True)

        # Layout for progress bar and label
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)

        # Staff buttons (initially empty)
        self.staff_buttons_layout = QHBoxLayout()

        # "Add staff" button
        self.add_staff_button = QPushButton("Add Staff")
        self.add_staff_button.clicked.connect(self.add_staff_click)

        # Staff name input box
        self.staff_name_input = QLineEdit()
        self.staff_name_input.setPlaceholderText("Enter staff name...")

        # Layout for "Add staff" button and input
        add_staff_layout = QHBoxLayout()
        add_staff_layout.addWidget(self.add_staff_button)
        add_staff_layout.addWidget(self.staff_name_input)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(self.staff_buttons_layout)
        main_layout.addLayout(add_staff_layout)

        self.setLayout(main_layout)

        # Fonts for visual enhancements
        font = QFont("Arial", 12)
        self.add_staff_button.setFont(font)
        self.staff_name_input.setFont(font)

    def add_staff_click(self):
        staff_name = self.staff_name_input.text().strip()
        if not staff_name:
            print("Please enter a staff name.")
            return

        self.add_staff(staff_name)

        # Emit signal for added staff, but only when the button was clicked
        self.staff_added.emit(staff_name)

    def add_staff(self, staff_name: str):
        # Create button for the new staff member
        staff_button = QPushButton(staff_name)
        staff_button.clicked.connect(self.start_progress)

        # Add button to layout and dictionary
        self.staff_buttons_layout.addWidget(staff_button)
        self.staff_buttons[staff_name] = staff_button

        # Clear input box
        self.staff_name_input.clear()

    def start_progress(self):
        sender = self.sender()  # Button object that sent the signal
        staff_name = sender.text()

        self.progress_bar.setValue(self.progress_bar.maximum())
        # Allow restarting progress for the same staff member
        if self.current_staff == staff_name and self.timer.isActive():
            return

        self.current_staff = staff_name
        self.progress_bar.setEnabled(True)
        self.progress_bar.setFormat(self.current_staff + "  %p%")

        if self.timer and self.timer.isActive():
            self.timer.stop()

        self.timer = QTimer(self)
        self.timer.setInterval(int(1000/self.timer_granularity_steps_per_seconds))  # 1-second interval
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()
        self.staff_selected.emit(self.current_staff)

    def update_progress(self):
        if self.progress_bar.value() > 0:
            self.progress_bar.setValue(self.progress_bar.value() - 1)
        else:
            # Progress bar finished, disable it and clear label, but allow restart
            self.current_staff = None
            self.progress_bar.setEnabled(False)
            self.progress_bar.setFormat("%p%")
            self.staff_selection_cleared.emit()
