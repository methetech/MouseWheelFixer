# gui/help_dialog.py
"""The help dialog for the application."""
from PyQt5 import QtWidgets, QtGui
import os

class HelpDialog(QtWidgets.QDialog):
    """The help dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QtWidgets.QApplication.instance().styleSheet())
        self.setWindowTitle("Scroll Lock Help")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "mouse.ico")))
        self.setMinimumSize(580, 460)

        layout = QtWidgets.QVBoxLayout(self)
        text_browser = QtWidgets.QTextBrowser()
        text_browser.setOpenExternalLinks(True)

        help_content = """
        <h1>WheelScrollFixer — Help</h1>
        <p>This app reduces accidental wheel scrolls by blocking rapid direction changes
        inside a short time window.</p>

        <h2>Blocking Logic</h2>
        <ul>
          <li><b>Block interval (s):</b> The time window during which opposite-direction
              wheel events are considered jitter and can be blocked.</li>
          <li><b>Direction change threshold:</b> Count of consecutive opposite events
              required within the interval to accept a deliberate change.</li>
        </ul>

        <h2>Application Control</h2>
        <ul>
          <li><b>Blacklist:</b> Executable names (e.g. <code>chrome.exe</code>) where
              blocking is disabled.</li>
          <li><b>Add Current App:</b> Quickly adds the foreground process to the blacklist.</li>
          <li><b>Start on boot:</b> Launches the app at Windows startup (with a watchdog).</li>
          <li><b>Enable Scroll Blocking:</b> Master switch.</li>
        </ul>

        <h2>Visual Feedback</h2>
        <p>A small “🚫” flashes near your cursor when an event is blocked.</p>

        <h2>Watchdog</h2>
        <p>If "Start on boot" is enabled, a detached watchdog will relaunch the app
        if it dies, ensuring continuity.</p>
        """
        text_browser.setHtml(help_content)
        layout.addWidget(text_browser)

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
