# wheel_entry.py
# Minimal PyQt5 tray application harness.
from __future__ import annotations

import sys
import signal
import atexit

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QTimer

APP_NAME = "MouseWheelFixer"


def _install_signal_handlers(app):
    def _quit(*_):
        app.quit()
    signal.signal(signal.SIGINT, _quit)
    signal.signal(signal.SIGTERM, _quit)


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    _install_signal_handlers(app)

    tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon())
    tray.setToolTip(APP_NAME)
    menu = QtWidgets.QMenu()
    act_quit = menu.addAction("Quit")
    act_quit.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()

    tick = QTimer()
    tick.setInterval(2000)
    tick.timeout.connect(lambda: None)
    tick.start()

    @atexit.register
    def _cleanup():
        try:
            tray.hide()
        except Exception:
            pass

    return app.exec_()
