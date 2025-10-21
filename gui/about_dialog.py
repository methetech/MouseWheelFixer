# gui/about_dialog.py
"""The about dialog for the application."""
from PyQt5 import QtWidgets, QtCore, QtGui
import os

class AboutDialog(QtWidgets.QDialog):
    """The about dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QtWidgets.QApplication.instance().styleSheet())
        self.setWindowTitle("About WheelScrollFixer")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "mouse.ico")))
        self.setFixedSize(340, 210)

        layout = QtWidgets.QVBoxLayout(self)

        app_name_label = QtWidgets.QLabel("<b>WheelScrollFixer</b>")
        app_name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(app_name_label)

        version_label = QtWidgets.QLabel("Version: 1.0.0")
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(version_label)

        author_label = QtWidgets.QLabel('Author: Me the Tech')
        author_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(author_label)

        description_label = QtWidgets.QLabel(
            'Specializing in AI Engineering, Automation, Architecture, Development, and Design. '
            'Combining thought and code for innovative technological solutions.'
        )
        description_label.setAlignment(QtCore.Qt.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        website_label = QtWidgets.QTextBrowser(self)
        website_label.setOpenExternalLinks(True)
        website_label.setHtml(
            '<p align="center"><a href="https://en.methetech.com/">en.methetech.com</a></p>'
        )
        website_label.setFixedHeight(30) # Adjust height to fit the link
        layout.addWidget(website_label)

        ok_button = QtWidgets.QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
