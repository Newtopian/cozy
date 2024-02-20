from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPlainTextEdit, QVBoxLayout, QWidget, QScrollArea, QGridLayout, QPushButton, QProgressBar, QInputDialog
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QTimer

class ChairWidget(QWidget):
    def __init__(self, chair_num, staff_section):
        super().__init__()

        self.chair_num = chair_num
        self.occupied = False
        self.occupied_time = None
        self.staff_section = staff_section

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel(f"Chair {self.chair_num}: Empty")
        layout.addWidget(self.label)

        self.occupant_edit = QPlainTextEdit(self)
        self.occupant_edit.setMaximumHeight(30)
        self.occupant_edit.setPlaceholderText("Enter occupant name")
        self.occupant_edit.textChanged.connect(self.updateOccupant)
        layout.addWidget(self.occupant_edit)

        self.setLayout(layout)

    def updateOccupant(self):
        if not self.occupied:
            occupant_name = self.occupant_edit.toPlainText().strip()
            self.label.setText(f"Chair {self.chair_num}: Empty - {occupant_name}")

        # Reset the timer on any chair action
        self.staff_section.resetTimer()

    def occupyChair(self):
        if not self.occupied:
            self.occupied = True
            self.occupied_time = datetime.now()
            occupant_name = self.occupant_edit.toPlainText().strip()
            self.label.setText(f"Chair {self.chair_num}: Occupied - {occupant_name} ({self.occupied_time})")

        # Reset the timer on chair occupation
        self.staff_section.resetTimer()

    def releaseChair(self):
        if self.occupied:
            self.occupied = False
            self.occupied_time = None
            self.label.setText(f"Chair {self.chair_num}: Empty")

        # Reset the timer on chair release
        self.staff_section.resetTimer()

    def occupantEditFinished(self):
        if self.occupant_edit.toPlainText().strip() != "":
            self.occupyChair()

class StaffSection(QWidget):
    def __init__(self):
        super().__init__()

        self.staff_members = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.add_staff_button = QPushButton("Add Staff", self)
        self.add_staff_button.clicked.connect(self.addStaffMember)
        layout.addWidget(self.add_staff_button)

        self.staff_buttons_layout = QVBoxLayout()

        self.timer_label = QLabel("Timer:")
        layout.addWidget(self.timer_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def addStaffMember(self):
        staff_name, ok = QInputDialog.getText(self, 'Add Staff Member', 'Enter Staff Member Name:')
        if ok and staff_name:
            staff_button = QPushButton(staff_name, self)
            staff_button.clicked.connect(self.startTimer)
            self.staff_buttons_layout.addWidget(staff_button)
            self.staff_members.append({'name': staff_name, 'button': staff_button})

    def startTimer(self):
        # Start the timer when a staff member button is clicked
        self.timer.start(100)  # 100 ms interval

    def resetTimer(self):
        # Reset the timer and progress bar
        self.timer.stop()
        self.progress_bar.setValue(100)
        self.timer.start(100)  # Restart the timer

    def updateTimer(self):
        # Update the progress bar value
        current_value = self.progress_bar.value()
        if current_value > 0:
            self.progress_bar.setValue(current_value - 1)
        else:
            # Stop the timer when it reaches 0
            self.timer.stop()
            self.progress_bar.setValue(100)

class ChairTrackingUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.chairs = {}
        self.staff_section = StaffSection()

        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        staff_widget = QWidget(self)
        staff_widget.setLayout(self.staff_section.staff_buttons_layout)
        layout.addWidget(staff_widget)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        scroll_content = QWidget(self)
        scroll_area.setWidget(scroll_content)

        grid_layout = QGridLayout(scroll_content)

        for row in range(1, 31):  # Assuming 60 chairs, you can adjust this based on your actual number of chairs
            for col in range(2):
                chair_num = (row - 1) * 2 + col + 1
                chair_widget = ChairWidget(chair_num, self.staff_section)
                grid_layout.addWidget(chair_widget, row, col)
                self.chairs[chair_num] = chair_widget

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Chair Tracking System')
        self.show()

if __name__ == '__main__':
    app = QApplication([])
    window = ChairTrackingUI()
    app.exec()
