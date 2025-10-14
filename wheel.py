# wheel.py
# Complete application with low-level mouse-wheel blocking, settings UI,
# tray menu, watchdog, single-instance guard, visual indicator, and
# an About dialog where en.MetheTech.com is a clickable link.
import sys
import winreg
import os
import subprocess
import logging
import configparser
import ctypes
from ctypes import wintypes

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.LPARAM),
    ]

import threading
import time
import psutil

import win32gui

import win32process
import win32con



from PyQt5 import QtWidgets, QtGui, QtCore

from PyQt5.QtCore import QSharedMemory



# =========================

# Custom INI Settings Class

# =========================

class IniSettings:

    def __init__(self, org_name, app_name):

        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", f"{app_name}.ini")

        self.config = configparser.ConfigParser()

        self._load_settings()



    def _load_settings(self):

        if os.path.exists(self.file_path):

            self.config.read(self.file_path)



    def value(self, key, default=None, type=None):

        section, option = self._parse_key(key)

        if self.config.has_option(section, option):

            val = self.config.get(section, option)

            if type == int:

                return int(val)

            elif type == float:

                return float(val)

            elif type == bool:

                return val.lower() == 'true'

            elif type == list:

                return eval(val) if val else [] # Safely evaluate list string

            elif type == dict:

                return eval(val) if val else {}

            return val

        return default



    def setValue(self, key, value):

        section, option = self._parse_key(key)

        if not self.config.has_section(section):

            self.config.add_section(section)

        

        # Convert lists and dicts to string representation for storage

        if isinstance(value, (list, dict)):

            self.config.set(section, option, repr(value))

        else:

            self.config.set(section, option, str(value))



    def _parse_key(self, key):

        # Simple key parsing for now, assuming no nested sections like QSettings

        # For QSettings compatibility, we might need to map 'group/key' to 'group' and 'key'

        if '/' in key:

            parts = key.split('/')

            return parts[0], parts[1]

        return 'General', key # Default section



    def sync(self):

        with open(self.file_path, 'w') as configfile:

            self.config.write(configfile)



# ===============

# App Settings

# ===============

class Settings(IniSettings):

    def __init__(self):

        super().__init__("ScrollLockApp", "Settings")

    # Blocking logic
    def get_interval(self) -> float:
        return self.value("block_interval", 0.50, type=float)  # default: 0.50s

    def set_interval(self, v: float):
        self.setValue("block_interval", v)

    def get_direction_change_threshold(self) -> int:
        return self.value("direction_change_threshold", 3, type=int)

    def set_direction_change_threshold(self, v: int):
        self.setValue("direction_change_threshold", v)

    # App control
    def get_blacklist(self):
        return self.value("blacklist", [], type=list)

    def set_blacklist(self, v):
        self.setValue("blacklist", v)

    def get_startup(self) -> bool:
        return self.value("start_on_boot", True, type=bool)

    def set_startup(self, v: bool):
        self.setValue("start_on_boot", v)

    def get_enabled(self) -> bool:
        return self.value("enabled", True, type=bool)

    def set_enabled(self, v: bool):
        self.setValue("enabled", v)

    # UI
    def get_font_size(self) -> float:
        return self.value("font_size", 10.0, type=float)

    def set_font_size(self, v: float):
        self.setValue("font_size", v)

    # Per-application profiles
    def get_app_profiles(self) -> dict:
        # Returns a dict like {'app_name.exe': {'interval': 0.3, 'threshold': 2}}
        return self.value("app_profiles", {}, type=dict)

    def set_app_profiles(self, v: dict):
        self.setValue("app_profiles", v)

    # Visual indicator settings
    def get_indicator_color(self) -> str:
        return self.value("indicator_color", "red", type=str) # Default to red

    def set_indicator_color(self, v: str):
        self.setValue("indicator_color", v)

    def get_indicator_size(self) -> int:
        return self.value("indicator_size", 36, type=int) # Default to 36px

    def set_indicator_size(self, v: int):
        self.setValue("indicator_size", v)


# ===========================
# Windows Startup Management
# ===========================
def configure_startup(enable: bool):
    """Create or remove HKCU Run entry for this script."""
    run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    name = "ScrollLockApp"
    path = f'{sys.executable} "{os.path.abspath(__file__)}"'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_WRITE) as key:
        if enable:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        else:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass


# ======================
# Visual Block Indicator
# ======================
class ScrollBlockIndicator(QtWidgets.QWidget):
    """A tiny overlay that flashes near the cursor when a scroll event is blocked."""
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setText("🚫")
        self.label.hide()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.setSingleShot(True)
        self.animation_timer.timeout.connect(self.hide_indicator)

        self.apply_settings()

    def apply_settings(self):
        color = self.settings.get_indicator_color()
        size = self.settings.get_indicator_size()
        self.label.setStyleSheet(f"font-size: {size}px; color: {color};")
        self.setFixedSize(size + 10, size + 10) # Add some padding around the emoji

    def show_indicator(self, pos: QtCore.QPoint):
        self.move(pos - QtCore.QPoint(self.width() // 2, self.height() // 2))
        self.label.show()
        self.show()
        self.animation_timer.start(500)

    def hide_indicator(self):
        self.label.hide()
        self.hide()


# =======================
# Low-Level Mouse Hooker
# =======================
class MouseHook:
    def __init__(self, settings: Settings, indicator: ScrollBlockIndicator = None):
        self.settings = settings
        self.indicator = indicator

        # cached settings
        self.block_interval = self.settings.get_interval()
        self.blacklist = self.settings.get_blacklist()
        self.app_profiles = self.settings.get_app_profiles()
        self.enabled = self.settings.get_enabled()
        self.direction_change_threshold = self.settings.get_direction_change_threshold()

        # state
        self.last_dir = None            # 1: up, -1: down
        self.last_time = 0.0
        self._consecutive_opposite_events = 0

        # debug counters
        self.blocked_up = 0
        self.blocked_down = 0

        # win32
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.hook_id = None
        self.hook_cb = None

    def reload_settings(self, update_tray_icon_callback=None, update_font_callback=None):
        self.block_interval = self.settings.get_interval()
        self.blacklist = self.settings.get_blacklist()
        self.app_profiles = self.settings.get_app_profiles()
        self.enabled = self.settings.get_enabled()
        self.direction_change_threshold = self.settings.get_direction_change_threshold()
        self._consecutive_opposite_events = 0
        if update_tray_icon_callback:
            update_tray_icon_callback()
        if update_font_callback:
            update_font_callback()

    def _get_current_app_settings(self):
        app_name = self.get_foreground_process_name()
        if app_name and app_name in self.app_profiles:
            profile = self.app_profiles[app_name]
            return profile.get('interval', self.block_interval), \
                   profile.get('threshold', self.direction_change_threshold)
        return self.block_interval, self.direction_change_threshold

    def is_blacklisted(self) -> bool:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid).name()
            return proc.lower() in (p.lower() for p in self.blacklist)
        except Exception:
            return False

    def start(self):
        # Callback type: LowLevelMouseProc
        CMPFUNC = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
        )

        def hook_proc(nCode, wParam, lParam):
            if nCode == 0 and wParam == win32con.WM_MOUSEWHEEL:
                if not self.enabled:
                    return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

                if self.is_blacklisted():
                    return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

                ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                # HIWORD(mouseData) contains the wheel delta, signed short
                delta_short = ctypes.c_short((ms.mouseData >> 16) & 0xFFFF).value
                current_dir = 1 if delta_short > 0 else -1

                now = time.time()

                current_block_interval, current_direction_change_threshold = self._get_current_app_settings()

                # First event or interval elapsed: establish (or re-establish) a direction
                if (self.last_dir is None) or (now - self.last_time >= current_block_interval):
                    self.last_dir = current_dir
                    self.last_time = now
                    self._consecutive_opposite_events = 0
                    return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

                # Within interval:
                if current_dir == self.last_dir:
                    # continuing same direction keeps the "burst" alive
                    self.last_time = now
                    self._consecutive_opposite_events = 0
                    return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
                else:
                    # opposite event inside interval
                    self._consecutive_opposite_events += 1
                    if self._consecutive_opposite_events >= current_direction_change_threshold:
                        # deliberate change — switch direction
                        self.last_dir = current_dir
                        self.last_time = now
                        self._consecutive_opposite_events = 0
                        return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
                    else:
                        # suppress the jitter
                        if current_dir > 0:
                            self.blocked_up += 1
                        else:
                            self.blocked_down += 1
                        if self.indicator:
                            self.indicator.show_indicator(QtGui.QCursor.pos())
                        return 1  # block

            return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

        self.hook_cb = CMPFUNC(hook_proc)
        self.hook_id = self.user32.SetWindowsHookExA(
            win32con.WH_MOUSE_LL,
            self.hook_cb,
            self.kernel32.GetModuleHandleW(None),
            0,
        )

        # Message loop (runs in this thread)
        msg = wintypes.MSG()
        while True:
            b = self.user32.GetMessageA(ctypes.byref(msg), None, 0, 0)
            if b == 0:  # WM_QUIT
                break
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageA(ctypes.byref(msg))


# =============
# Help Dialog
# =============
class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QtWidgets.QApplication.instance().styleSheet())
        self.setWindowTitle("Scroll Lock Help")
        self.setMinimumSize(580, 460)

        layout = QtWidgets.QVBoxLayout(self)
        text_browser = QtWidgets.QTextBrowser()
        text_browser.setOpenExternalLinks(True)

        help_content = """
        <h1>Scroll Lock Application — Help</h1>
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


# ==============
# About Dialog
# ==============
class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QtWidgets.QApplication.instance().styleSheet())
        self.setWindowTitle("About Scroll Lock App")
        self.setFixedSize(340, 210)

        layout = QtWidgets.QVBoxLayout(self)

        app_name_label = QtWidgets.QLabel("<b>Scroll Lock App</b>")
        app_name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(app_name_label)

        version_label = QtWidgets.QLabel("Version: 1.0.0")
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(version_label)

        author_label = QtWidgets.QLabel('Author: Me the Tech')
        author_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(author_label)

        description_label = QtWidgets.QLabel('Specializing in AI Engineering, Automation, Architecture, Development, and Design. Combining thought and code for innovative technological solutions.')
        description_label.setAlignment(QtCore.Qt.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        website_label = QtWidgets.QTextBrowser(self)
        website_label.setOpenExternalLinks(True)
        website_label.setHtml('<p align="center"><a href="https://en.methetech.com/">en.methetech.com</a></p>')
        website_label.setFixedHeight(30) # Adjust height to fit the link
        layout.addWidget(website_label)

        ok_button = QtWidgets.QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)


class AppProfileDialog(QtWidgets.QDialog):
    def __init__(self, current_app_name: str = "", current_interval: float = 0.5, current_threshold: int = 3, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Profile")
        self.setFixedSize(300, 200)
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

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
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
        return {
            "app_name": self.app_name_input.text(),
            "interval": self.interval_spin.value(),
            "threshold": self.threshold_spin.value()
        }


# =================
# Settings Dialog
# =================
class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings: Settings, hook: MouseHook,
                 update_tray_icon_callback, update_font_callback, tray: QtWidgets.QSystemTrayIcon):
        super().__init__()
        # Keep your original flag (adds "?") on titlebar)
        self.setWindowFlags(
            self.windowFlags() 
            | QtCore.Qt.WindowContextHelpButtonHint 
            | QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setWindowTitle('Scroll Lock Settings')
        self.settings = settings
        self.hook = hook
        self.update_tray_icon_callback = update_tray_icon_callback
        self.update_font_callback = update_font_callback
        self.tray = tray

        icon_path = os.path.join(os.path.dirname(__file__), "mouse.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        # Menu Bar
        menu_bar = QtWidgets.QMenuBar(self)
        help_menu = menu_bar.addMenu("&Help")
        act_about = help_menu.addAction("&About")
        act_documentation = help_menu.addAction("&Website")
        act_help_content = help_menu.addAction("Help &Content")
        # [ADDED] explicit "What's This" mode command (Shift+F1 standard)
        act_whats_this = help_menu.addAction("What's &This?")
        act_whats_this.setShortcut(QtGui.QKeySequence("Shift+F1"))
        act_whats_this.triggered.connect(QtWidgets.QWhatsThis.enterWhatsThisMode)

        act_about.triggered.connect(self.show_about_dialog)
        act_documentation.triggered.connect(self.open_website)
        act_help_content.triggered.connect(self.show_help_dialog)

        # Widgets
        self.interval_spin = QtWidgets.QDoubleSpinBox()
        self.interval_spin.setRange(0.05, 5.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(self.settings.get_interval())
        self.interval_spin.setToolTip('The time interval (in seconds) during which rapid scroll direction changes will be blocked. Prevents accidental scrolling.')
        self.interval_spin.setWhatsThis('This setting controls the time window (in seconds) for blocking rapid changes in scroll direction. If you scroll in one direction, and then quickly scroll in the opposite direction within this interval, the second scroll event will be ignored. This helps prevent "jittery" or accidental scrolling.')

        self.bl_list = QtWidgets.QListWidget()
        self.bl_list.addItems(self.settings.get_blacklist())
        self.bl_list.setToolTip('List of application executable names (e.g., chrome.exe) where scroll blocking will be disabled.')
        self.bl_list.setWhatsThis('This list displays application executable names (e.g., chrome.exe, notepad.exe) for which the scroll blocking functionality will be completely disabled. This is useful for applications where you need precise or unrestricted scrolling.')

        self.bl_add_current_btn = QtWidgets.QPushButton('Add Current App')
        self.bl_add_current_btn.setToolTip("Add the foreground process.")
        self.bl_add_current_btn.setWhatsThis('Click to add the currently focused application\'s executable name to the blacklist so scrolling is not blocked in that app.')

        self.bl_remove_btn = QtWidgets.QPushButton("Remove Selected")
        self.bl_remove_btn.setToolTip("Remove selected blacklist entries.")
        self.bl_remove_btn.setWhatsThis('Removes the selected application(s) from the blacklist, re-enabling scroll blocking for them.')

        self.bl_clear_btn = QtWidgets.QPushButton("Clear All")
        self.bl_clear_btn.setToolTip("Clear blacklist.")
        self.bl_clear_btn.setWhatsThis('Clears the entire blacklist. Scroll blocking will apply to all apps unless added again.')

        self.start_cb = QtWidgets.QCheckBox("Start on boot")
        self.start_cb.setChecked(self.settings.get_startup())
        self.start_cb.setToolTip('If checked, the application will start automatically when Windows boots.')
        self.start_cb.setWhatsThis('If checked, the main application and its child watchdog process will start automatically when Windows boots. This ensures the scroll blocking functionality is always active.')

        

        self.enabled_cb = QtWidgets.QCheckBox('Enable Scroll Blocking')
        self.enabled_cb.setChecked(self.settings.get_enabled())
        self.enabled_cb.setToolTip('Master switch to enable or disable the scroll blocking functionality.')
        self.enabled_cb.setWhatsThis('This is a master switch to globally enable or disable the scroll blocking functionality. When unchecked, no scroll events will be blocked, regardless of other settings.')

        self.direction_change_threshold_spin = QtWidgets.QSpinBox()
        self.direction_change_threshold_spin.setRange(1, 10)
        self.direction_change_threshold_spin.setValue(self.settings.get_direction_change_threshold())
        self.direction_change_threshold_spin.setToolTip('The number of consecutive opposite scroll events required to re-establish a new scroll direction within the block interval.')
        self.direction_change_threshold_spin.setWhatsThis('The number of consecutive opposite scroll events required to "break" the current blocking and establish a new scroll direction within the block interval. This allows for deliberate, quick changes in scroll direction if you scroll aggressively enough.')

        self.font_size_spin = QtWidgets.QDoubleSpinBox()
        self.font_size_spin.setRange(8.0, 24.0) # Reasonable font size range
        self.font_size_spin.setSingleStep(0.5)
        self.font_size_spin.setValue(self.settings.get_font_size())
        self.font_size_spin.setToolTip('Adjust the global font size for the application UI.')
        self.font_size_spin.setWhatsThis('Adjust the global font size for the application user interface. This affects the size of text and elements within the application windows.')

        self.save_btn = QtWidgets.QPushButton('Save')
        self.save_btn.setToolTip("Save all settings.")
        self.save_btn.setWhatsThis('Saves all changes to persistent settings, applies them immediately to the running hook, and updates the tray UI as needed.')

        # Layout: Blocking Logic
        blocking_group = QtWidgets.QGroupBox("Blocking Logic")
        blocking_group.setWhatsThis('Parameters that control how scroll blocking behaves.')
        blocking_layout = QtWidgets.QFormLayout()
        blocking_layout.addRow("Block interval (s):", self.interval_spin)
        blocking_layout.addRow("Direction change threshold:", self.direction_change_threshold_spin)
        blocking_group.setLayout(blocking_layout)

        # Layout: App Control
        app_control_group = QtWidgets.QGroupBox("Application Control")
        app_control_group.setWhatsThis('Manage where the blocker is disabled (blacklist).')
        app_control_layout = QtWidgets.QVBoxLayout()
        app_control_layout.addWidget(self.bl_list)
        bl_buttons_layout = QtWidgets.QHBoxLayout()
        bl_buttons_layout.addWidget(self.bl_add_current_btn)
        bl_buttons_layout.addWidget(self.bl_remove_btn)
        bl_buttons_layout.addWidget(self.bl_clear_btn)
        app_control_layout.addLayout(bl_buttons_layout)
        app_control_group.setLayout(app_control_layout)

        # Layout: General
        general_settings_group = QtWidgets.QGroupBox("General Settings")
        general_settings_group.setWhatsThis('Startup behavior, master enable, and UI font size.')
        general_settings_layout = QtWidgets.QFormLayout()
        general_settings_layout.addRow(self.start_cb)
        general_settings_layout.addRow(self.enabled_cb)
        general_settings_layout.addRow("Font size (pt):", self.font_size_spin)

        self.indicator_color_btn = QtWidgets.QPushButton("Choose Color")
        self.indicator_color_btn.clicked.connect(self.choose_indicator_color)
        self.indicator_color_btn.setToolTip('Choose the color for the scroll block indicator.')
        self.indicator_color_btn.setWhatsThis('Click to open a color dialog and select the color for the visual scroll block indicator.')
        general_settings_layout.addRow("Indicator Color:", self.indicator_color_btn)

        self.indicator_size_spin = QtWidgets.QSpinBox()
        self.indicator_size_spin.setRange(16, 128) # Reasonable range for indicator size
        self.indicator_size_spin.setValue(self.settings.get_indicator_size())
        self.indicator_size_spin.setToolTip('Adjust the size of the scroll block indicator.')
        self.indicator_size_spin.setWhatsThis('Adjust the size (in pixels) of the visual scroll block indicator.')
        general_settings_layout.addRow("Indicator Size:", self.indicator_size_spin)

        general_settings_group.setLayout(general_settings_layout)

        # Main form layout
        form = QtWidgets.QFormLayout(self)
        form.setMenuBar(menu_bar)
        form.addRow(blocking_group)
        form.addRow(app_control_group)

        # Layout: Application Profiles
        app_profiles_group = QtWidgets.QGroupBox("Application Profiles")
        app_profiles_group.setWhatsThis('Define custom scroll blocking settings for specific applications.')
        app_profiles_layout = QtWidgets.QVBoxLayout()
        self.app_profiles_list = QtWidgets.QListWidget()
        app_profiles_layout.addWidget(self.app_profiles_list)
        app_profiles_buttons_layout = QtWidgets.QHBoxLayout()
        self.add_profile_btn = QtWidgets.QPushButton('Add Profile')
        self.edit_profile_btn = QtWidgets.QPushButton('Edit Profile')
        self.remove_profile_btn = QtWidgets.QPushButton('Remove Profile')
        app_profiles_buttons_layout.addWidget(self.add_profile_btn)
        app_profiles_buttons_layout.addWidget(self.edit_profile_btn)
        app_profiles_buttons_layout.addWidget(self.remove_profile_btn)
        app_profiles_layout.addLayout(app_profiles_buttons_layout)
        app_profiles_group.setLayout(app_profiles_layout)
        form.addRow(app_profiles_group)

        form.addRow(general_settings_group)
        form.addRow(self.save_btn)

        # [ADDED] What's-this for menu bar and actions themselves (so clicks in help mode on menu show tips)
        menu_bar.setWhatsThis('Application help menu. Use “What’s This?” then click any control to learn about it.')
        help_menu.setWhatsThis('Help menu — access About, Website, Help Content, and What’s This mode.')
        act_about.setWhatsThis('Show information about this application.')
        act_documentation.setWhatsThis('Open the project website in your default browser.')
        act_help_content.setWhatsThis('Open the in-app Help dialog with a detailed explanation.')
        act_whats_this.setWhatsThis('Enter What’s This mode (same as clicking the “?” on the titlebar).')

        # Signals
        self.save_btn.clicked.connect(self.save)
        
        self.bl_add_current_btn.clicked.connect(self.add_current_app_to_blacklist)
        self.bl_remove_btn.clicked.connect(self.remove_selected_from_blacklist)
        self.bl_clear_btn.clicked.connect(self.clear_blacklist)

        # Initialize app profiles list
        self.refresh_app_profiles_list()

        # Connect app profile buttons
        self.add_profile_btn.clicked.connect(self.add_app_profile)
        self.edit_profile_btn.clicked.connect(self.edit_app_profile)
        self.remove_profile_btn.clicked.connect(self.remove_app_profile)

    def minimize_to_tray(self):
        self.hide()
        # Show a message from the tray icon
        self.tray.showMessage(
            "Scroll Lock App",
            "Application minimized to tray. Click the icon to restore.",
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "mouse.ico")),
            2000 # 2 seconds
        )

    def closeEvent(self, event):
        QtWidgets.qApp.quit()

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimize_to_tray()
        super().changeEvent(event)

    def refresh_app_profiles_list(self):
        self.app_profiles_list.clear()
        for app_name, profile in self.settings.get_app_profiles().items():
            interval = profile.get('interval', self.settings.get_interval())
            threshold = profile.get('threshold', self.settings.get_direction_change_threshold())
            self.app_profiles_list.addItem(f"{app_name}: Interval={interval:.2f}s, Threshold={threshold}")

    def add_app_profile(self):
        dialog = AppProfileDialog(parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_profile_data()
            app_name = data['app_name'].lower()
            if not app_name:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Application name cannot be empty.")
                return

            profiles = self.settings.get_app_profiles()
            profiles[app_name] = {
                'interval': data['interval'],
                'threshold': data['threshold']
            }
            self.settings.set_app_profiles(profiles)
            self.refresh_app_profiles_list()
            self.hook.reload_settings(self.update_tray_icon_callback, self.update_font_callback)

    def edit_app_profile(self):
        selected_items = self.app_profiles_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a profile to edit.")
            return

        selected_item = selected_items[0]
        item_text = selected_item.text()
        app_name_raw = item_text.split(':')[0].strip()
        app_name = app_name_raw.lower()

        profiles = self.settings.get_app_profiles()
        profile_data = profiles.get(app_name, {})

        dialog = AppProfileDialog(
            current_app_name=app_name_raw,
            current_interval=profile_data.get('interval', self.settings.get_interval()),
            current_threshold=profile_data.get('threshold', self.settings.get_direction_change_threshold()),
            parent=self
        )

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_profile_data()
            new_app_name = data['app_name'].lower()
            if not new_app_name:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Application name cannot be empty.")
                return

            # If app name changed, remove old entry
            if new_app_name != app_name:
                del profiles[app_name]

            profiles[new_app_name] = {
                'interval': data['interval'],
                'threshold': data['threshold']
            }
            self.settings.set_app_profiles(profiles)
            self.refresh_app_profiles_list()
            self.hook.reload_settings(self.update_tray_icon_callback, self.update_font_callback)

    def remove_app_profile(self):
        selected_items = self.app_profiles_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a profile to remove.")
            return

        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Removal", "Are you sure you want to remove the selected profile(s)?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            profiles = self.settings.get_app_profiles()
            for item in selected_items:
                app_name = item.text().split(':')[0].strip().lower()
                if app_name in profiles:
                    del profiles[app_name]
            self.settings.set_app_profiles(profiles)
            self.refresh_app_profiles_list()
            self.hook.reload_settings(self.update_tray_icon_callback, self.update_font_callback)

    def choose_indicator_color(self):
        initial_color = QtGui.QColor(self.settings.get_indicator_color())
        color = QtWidgets.QColorDialog.getColor(initial_color, self, "Select Indicator Color")
        if color.isValid():
            self.settings.set_indicator_color(color.name())
            # Update the button's background to show selected color
            self.indicator_color_btn.setStyleSheet(f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'};")

    def show_help_dialog(self):
        HelpDialog(self).exec_()

    def show_about_dialog(self):
        AboutDialog(self).exec_()

    def open_website(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://en.MetheTech.com"))

    def get_foreground_process_name(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def add_current_app_to_blacklist(self):
        # Hide briefly so the dialog isn't the foreground window
        self.hide()
        QtCore.QTimer.singleShot(120, self._get_and_add_foreground_app)

    def _get_and_add_foreground_app(self):
        proc_name = self.get_foreground_process_name()
        existing = [self.bl_list.item(i).text() for i in range(self.bl_list.count())]
        if proc_name and proc_name not in existing:
            self.bl_list.addItem(proc_name)
        self.show()

    def remove_selected_from_blacklist(self):
        for item in self.bl_list.selectedItems():
            self.bl_list.takeItem(self.bl_list.row(item))

    def clear_blacklist(self):
        self.bl_list.clear()

    def save(self):
        self.settings.set_interval(self.interval_spin.value())
        bl = [self.bl_list.item(i).text() for i in range(self.bl_list.count())]
        self.settings.set_blacklist(bl)
        self.settings.set_startup(self.start_cb.isChecked())
        configure_startup(self.start_cb.isChecked())
        
        self.settings.set_enabled(self.enabled_cb.isChecked())
        self.settings.set_direction_change_threshold(self.direction_change_threshold_spin.value())
        self.settings.set_font_size(self.font_size_spin.value())
        self.settings.set_indicator_color(self.settings.get_indicator_color()) # Save the chosen color
        self.settings.set_indicator_size(self.indicator_size_spin.value()) # Save the chosen size

        # Explicitly sync settings to INI file
        self.settings.sync()

        # Apply settings live
        self.hook.reload_settings(self.update_tray_icon_callback, self.update_font_callback)
        QtWidgets.QMessageBox.information(self, "Saved", "Settings saved.")


# =====================
# Watchdog (child proc)
# =====================
def child_watchdog_process(parent_pid: int):
    """Relaunch the script if the parent dies, unless a graceful shutdown was initiated."""
    script_path = os.path.abspath(__file__)
    shutdown_flag_id = "ScrollLockApp_ShutdownFlag"
    shutdown_memory = QSharedMemory(shutdown_flag_id)

    # Watchdog needs to attach to the shared memory created by the main app
    if not shutdown_memory.attach():
        print("[Watchdog] Could not attach to shutdown shared memory. Exiting.")
        sys.exit(1) # Exit if cannot attach, as graceful shutdown won't work

    while True:
        # Check if the main app initiated a graceful shutdown
        shutdown_memory.lock()
        ptr = shutdown_memory.constData()
        if ptr:
            address = int(ptr)
            buffer = ctypes.cast(address, ctypes.POINTER(ctypes.c_char))
            flag_value = buffer[0]
        else:
            flag_value = 0
        shutdown_memory.unlock()

        if flag_value == b'\x01': # If the flag is 1 (true)
            print(f"[Watchdog] Parent {parent_pid} gracefully shut down. Exiting watchdog.")
            sys.exit(0)

        try:
            if not psutil.pid_exists(parent_pid):
                print(f"[Watchdog] Parent {parent_pid} died unexpectedly. Relaunching...")
                subprocess.Popen(
                    [sys.executable, script_path],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                )
                sys.exit(0)
        except Exception as e:
            print(f"[Watchdog] Error: {e}")
        time.sleep(5)


# =========
#  main()
# =========
def main():
    # Watchdog child?
    if len(sys.argv) > 1 and sys.argv[1] == "--watchdog":
        parent_pid = int(sys.argv[2])
        child_watchdog_process(parent_pid)
        return

    logging.info('Creating QApplication')
    app = QtWidgets.QApplication(sys.argv)

    settings = Settings()
    logging.info('Settings loaded')

    # Apply global font size
    def apply_global_font():
        font = QtGui.QFont()
        font.setPointSize(int(settings.get_font_size()))
        app.setFont(font)

    apply_global_font()
    logging.info('Font applied')

    # Apply modern stylesheet
    app.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 10pt;
        }
        QPushButton {
            background-color: #0078D7;
            color: white;
            border: 1px solid #0078D7; /* Use primary color for border */
            border-radius: 4px; /* Slightly more rounded corners */
            padding: 6px 18px; /* Slightly more padding */
            min-width: 80px; /* Ensure minimum width for consistency */
        }
        QPushButton:hover {
            background-color: #0056B3;
            border-color: #0056B3;
        }
        QPushButton:pressed {
            background-color: #003f80;
            border-color: #003f80;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 20px; /* Increased margin-top for better separation */
            border: 1px solid #D0D0D0; /* Lighter border */
            border-radius: 6px; /* Slightly more rounded corners */
            padding-top: 25px; /* Increased padding-top to accommodate title */
            padding-bottom: 10px;
            padding-left: 10px;
            padding-right: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; /* Position title at top left */
            padding: 0 5px; /* Padding around title text */
            left: 10px; /* Offset title from the left edge */
            margin-left: 2px;
            color: #333333; /* Darker color for title */
            background-color: transparent; /* Ensure title background is transparent */
        }
        QSpinBox, QDoubleSpinBox {
            border: 1px solid #D0D0D0;
            border-radius: 4px;
            padding: 3px;
            background-color: #FFFFFF;
            selection-background-color: #0078D7;
            selection-color: white;
        }
        QListWidget {
            border: 1px solid #D0D0D0;
            border-radius: 4px;
            background-color: #FFFFFF;
            selection-background-color: #0078D7;
            selection-color: white;
            padding: 2px;
        }
        QMenuBar {
            background-color: #f0f0f0;
            border-bottom: 1px solid #ccc;
        }
        QMenuBar::item {
            padding: 5px 10px;
            background-color: transparent;
        }
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        QMenu {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
        }
        QMenu::item {
            padding: 5px 20px 5px 10px;
        }
        QMenu::item:selected {
            background-color: #0078D7;
            color: white;
        }
    """)
    logging.info('Stylesheet applied')

    # Single instance guard
    app_id = "ScrollLockApp_SingleInstance"
    shared_memory = QSharedMemory(app_id)
    if not shared_memory.create(1):
        logging.warning('Another instance is already running')
        QtWidgets.QMessageBox.information(
            None, "Already running", "Another instance of ScrollLockApp is already running."
        )
        sys.exit(0)
    logging.info('Single instance guard passed')

    # Watchdog shutdown flag
    shutdown_flag_id = "ScrollLockApp_ShutdownFlag"
    shutdown_memory = QSharedMemory(shutdown_flag_id)

    # Try to attach first. If it exists, clear the flag.
    if shutdown_memory.attach():
        shutdown_memory.lock()
        buffer = shutdown_memory.data()
        buffer.setData(b'\0') # Clear the flag (set to 0)
        shutdown_memory.unlock()
        logging.info('Cleared existing shutdown flag')
        # Do NOT detach here. Main app should remain attached.
    else:
        # If it doesn't exist, try to create it
        if not shutdown_memory.create(1): # Create 1 byte for the flag
            logging.error('Could not create shutdown shared memory')
            print("[Main] Could not create shutdown shared memory. Watchdog shutdown might not work correctly.")
            # Proceed, but log the error. The app might still run, but watchdog shutdown won't be graceful.
        else:
            logging.info('Created shutdown shared memory')

    # Visual indicator
    indicator = ScrollBlockIndicator(settings)
    logging.info('Visual indicator created')

    # Hook
    hook = MouseHook(settings, indicator)
    logging.info('Mouse hook created')

    # Spawn watchdog if configured
    if settings.get_startup() and "--no-watchdog" not in sys.argv:
        try:
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "--watchdog", str(os.getpid())],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            logging.info('Watchdog process spawned')
        except Exception as e:
            # Non-fatal
            logging.error(f'Watchdog spawn failed: {e}')
            print(f"[Main] Watchdog spawn failed: {e}")

    # Start hook thread
    t = threading.Thread(target=hook.start, daemon=True)
    t.start()
    logging.info('Hook thread started')

    # Tray icon + menu
    icon_path = os.path.join(os.path.dirname(__file__), "mouse.ico")
    tray_icon = QtGui.QIcon(icon_path) if os.path.exists(icon_path) else QtGui.QIcon()
    logging.info('Tray icon loaded')

    tray = QtWidgets.QSystemTrayIcon(tray_icon, parent=app)

    # We'll reuse the same icon. If you ship multiple icons, you can branch here.
    def update_tray_icon():
        tray.setIcon(tray_icon)

    update_tray_icon()
    logging.info('Tray icon updated')

    menu = QtWidgets.QMenu()
    act_settings = menu.addAction("Settings")
    act_toggle_enabled = menu.addAction("Toggle Scroll Blocking")
    act_help = menu.addAction("Help")
    act_about = menu.addAction("About")
    menu.addSeparator()
    act_exit = menu.addAction("Exit")
    tray.setContextMenu(menu)
    tray.setToolTip("Scroll Lock App")
    tray.show()
    logging.info('Tray icon shown')

    # Settings dialog
    dlg = SettingsDialog(settings, hook, update_tray_icon, apply_global_font, tray)
    act_settings.triggered.connect(dlg.show)
    logging.info('Settings dialog created')

    # [ADDED] Give tray actions What’s This strings (useful if you later expose them in a window)
    act_settings.setWhatsThis("Open the Settings window to configure blocking and UI options.")
    act_toggle_enabled.setWhatsThis("Enable/disable scroll blocking globally.")
    act_help.setWhatsThis("Open the Help dialog.")
    act_about.setWhatsThis("Open the About dialog.")
    act_exit.setWhatsThis("Quit the application.")

    # Actions
    def toggle_enabled_from_tray():
        current_state = settings.get_enabled()
        settings.set_enabled(not current_state)
        hook.reload_settings(update_tray_icon, apply_global_font)
        update_tray_icon()
        QtWidgets.QMessageBox.information(
            None,
            "Scroll Blocking",
            f"Scroll blocking is now: {'Enabled' if not current_state else 'Disabled'}.",
        )

    act_toggle_enabled.triggered.connect(toggle_enabled_from_tray)

    def show_help_dialog():
        HelpDialog(dlg).exec_()

    def show_about_dialog():
        AboutDialog(dlg).exec_()

    act_help.triggered.connect(show_help_dialog)
    act_about.triggered.connect(show_about_dialog)
    act_exit.triggered.connect(QtWidgets.qApp.quit)

    # Show settings on start
    dlg.show()
    logging.info('Settings dialog hidden and tray message shown')

    # Restore window on tray icon click
    def restore_window(reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            dlg.showNormal()
            dlg.activateWindow()

    tray.activated.connect(restore_window)

    # Persist settings on exit and set shutdown flag
    def on_about_to_quit():
        logging.info('Application quitting')
        settings.sync()
        # Set the shutdown flag
        if shutdown_memory.isAttached() or shutdown_memory.attach():
            shutdown_memory.lock()
            ptr = shutdown_memory.data()
            if ptr:
                address = int(ptr)
                buffer = ctypes.cast(address, ctypes.POINTER(ctypes.c_char))
                buffer[0] = b'\x01'
            shutdown_memory.unlock()
            logging.info('Shutdown flag set')

    app.aboutToQuit.connect(on_about_to_quit)

    logging.info('Starting event loop')
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()