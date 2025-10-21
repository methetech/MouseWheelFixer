# gui/app_profile_dialog.py
"""The application profile dialog for the application."""
import psutil
import win32gui
import win32process
from PyQt5 import QtWidgets, QtGui
import os

class AppProfileDialog(QtWidgets.QDialog):
    """The application profile dialog."""
    def __init__(self, current_app_name: str = "", current_interval: float = 0.5, current_threshold: int = 3, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Profile")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "mouse.ico")))
        self.setMinimumSize(400, 220)
        self.setStyleSheet(QtWidgets.QApplication.instance().styleSheet())

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()

        self.app_name_input = QtWidgets.QLineEdit(current_app_name)
        self.app_name_input.setPlaceholderText("e.g., chrome.exe")
        form_layout.addRow("Application Name:", self.app_name_input)

        self.get_current_app_btn = QtWidgets.QPushButton("Get Current App")
        self.get_current_app_btn.clicked.connect(self._get_current_app)
        form_layout.addRow("", self.get_current_app_btn)

        self.interval_spin = QtWidgets.QDoubleSpinBox()
        self.interval_spin.setRange(0.05, 5.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(current_interval)
        form_layout.addRow("Block Interval (s):", self.interval_spin)

        self.threshold_spin = QtWidgets.QSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setValue(current_threshold)
        form_layout.addRow("Direction Change Threshold:", self.threshold_spin)

        layout.addLayout(form_layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _get_current_app(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name()
            self.app_name_input.setText(proc_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            QtWidgets.QMessageBox.warning(self, "Error", "Could not get foreground application name.")

    def get_profile_data(self):
        """Gets the profile data from the dialog."""
        return {
            "app_name": self.app_name_input.text(),
            "interval": self.interval_spin.value(),
            "threshold": self.threshold_spin.value()
        }
