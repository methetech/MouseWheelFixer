# wheel.py
# Complete application with low-level mouse-wheel blocking, settings UI,
# tray menu, watchdog, single-instance guard, and
# an About dialog where en.MetheTech.com is a clickable link.
import sys
import winreg
import os
import subprocess
import logging
import configparser
import ctypes
import ast
import threading
import time
import tempfile
import atexit
import platform
from ctypes import wintypes

import psutil
import win32gui
import win32process
import win32con
from PyQt5 import QtWidgets, QtGui, QtCore
from app_context import AppContext
from gui import SettingsDialog, HelpDialog, AboutDialog

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.LPARAM),
    ]



# =========================

# Custom INI Settings Class

# =========================

class IniSettings:

    """A custom INI file settings manager."""

    def __init__(self, org_name, app_name):

        """Initializes the settings, loading from the INI file."""

        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", f"{app_name}.ini")

        self.config = configparser.ConfigParser()

        self._load_settings()



    def _load_settings(self):

        """Loads settings from the INI file if it exists."""

        if os.path.exists(self.file_path):

            self.config.read(self.file_path)



    def value(self, key, default=None, type=None):

        """Retrieves a value from the settings."""

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

                return ast.literal_eval(val) if val else [] # Safely evaluate list string

            elif type == dict:

                return ast.literal_eval(val) if val else {}

            return val

        return default



    def set_value(self, key, value):

        """Sets a value in the settings."""

        section, option = self._parse_key(key)

        if not self.config.has_section(section):

            self.config.add_section(section)

        

        # Convert lists and dicts to string representation for storage

        if isinstance(value, (list, dict)):

            self.config.set(section, option, repr(value))

        else:

            self.config.set(section, option, str(value))



    def _parse_key(self, key):

        """Parses a key into a section and option."""

        # Simple key parsing for now, assuming no nested sections like QSettings

        # For QSettings compatibility, we might need to map 'group/key' to 'group' and 'key'

        if '/' in key:

            parts = key.split('/')

            return parts[0], parts[1]

        return 'General', key # Default section



    def sync(self):

        """Saves the settings to the INI file."""

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        with open(self.file_path, 'w', encoding='utf-8') as configfile:

            self.config.write(configfile)

# gui/single_instance.py
# Robust Windows single-instance guard using a named mutex.
# Automatically released by the OS on crash/exit (no stale files).
def bring_window_to_front(window_title):
    """Finds a window by its title and brings it to the foreground."""
    try:
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            # Restore the window if it's minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # Bring the window to the foreground
            win32gui.SetForegroundWindow(hwnd)
            return True
    except Exception as e:
        print(f"Error bringing window to front: {e}")
    return False

class SingleInstance:
    """
    Ensures only a single instance of the application is running using a named mutex.
    If another instance is found, it brings its main window to the front.
    """
    def __init__(self, app_name, window_title):
        self.mutex = None
        self.mutex_name = f"Global\\{app_name}_Mutex"
        self.window_title = window_title

    def acquire_lock(self):
        """
        Attempts to acquire the mutex. If it fails, another instance is running.
        In that case, it brings the existing window to the front and returns False.
        Returns True if the lock was acquired successfully.
        """
        self.mutex = ctypes.windll.kernel32.CreateMutexW(None, True, self.mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
            print("Another instance is already running. Bringing it to the front.")
            bring_window_to_front(self.window_title)
            return False # Lock not acquired
        return True # Lock acquired

    def release_lock(self):
        """Releases the mutex."""
        if self.mutex:
            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None

    def __del__(self):
        self.release_lock()

# ===============
# App Settings
# ===============
class Settings(IniSettings):
    """Manages application-specific settings."""
    def __init__(self):
        """Initializes the application settings."""
        super().__init__("ScrollLockApp", "Settings")

    # Blocking logic
    def get_interval(self) -> float:
        """Gets the block interval in seconds."""
        return self.value("block_interval", 0.3, type=float)  # default: 0.3s

    def set_interval(self, v: float):
        """Sets the block interval in seconds."""
        self.set_value("block_interval", v)

    def get_direction_change_threshold(self) -> int:
        """Gets the direction change threshold."""
        return self.value("direction_change_threshold", 2, type=int)

    def set_direction_change_threshold(self, v: int):
        """Sets the direction change threshold."""
        self.set_value("direction_change_threshold", v)

    # App control
    def get_blacklist(self):
        """Gets the list of blacklisted applications."""
        return self.value("blacklist", [], type=list)

    def set_blacklist(self, v):
        """Sets the list of blacklisted applications."""
        self.set_value("blacklist", v)

    def get_startup(self) -> bool:
        """Gets the startup on boot setting."""
        return self.value("start_on_boot", False, type=bool)

    def set_startup(self, v: bool):
        """Sets the startup on boot setting."""
        self.set_value("start_on_boot", v)

    def get_enabled(self) -> bool:
        """Gets the enabled state of the application."""
        return self.value("enabled", True, type=bool)

    def set_enabled(self, v: bool):
        """Sets the enabled state of the application."""
        self.set_value("enabled", v)

    # UI
    def get_font_size(self) -> float:
        """Gets the font size."""
        return self.value("font_size", 10.0, type=float)

    def set_font_size(self, v: float):
        """Sets the font size."""
        self.set_value("font_size", v)

    # Per-application profiles
    def get_app_profiles(self) -> dict:
        """Gets the application profiles."""
        # Returns a dict like {'app_name.exe': {'interval': 0.3, 'threshold': 2}}
        return self.value("app_profiles", {}, type=dict)

    def set_app_profiles(self, v: dict):
        """Sets the application profiles."""
        self.set_value("app_profiles", v)




# ===========================
# Windows Startup Management
# ===========================
def configure_startup(enable: bool):
    """Create or remove HKCU Run entry for this script."""
    run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    name = "ScrollLockApp"
    path = f'"{os.path.abspath(sys.executable)}" "{os.path.abspath(__file__)}"'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_WRITE) as key:
        if enable:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        else:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass





# =======================
# Low-Level Mouse Hooker
# =======================
class MouseHook:
    def __init__(self, settings: Settings):
        self.settings = settings
        

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
        app_name = get_foreground_process_name()
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
        except (psutil.NoSuchProcess, psutil.AccessDenied):
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






# =========
#  main()
# =========
def main():


    # Single instance guard
    app_name = "MouseWheelFixer"
    window_title = "Scroll Lock Settings"
    single_instance = SingleInstance(app_name, window_title)
    if not single_instance.acquire_lock():
        sys.exit(0) # Another instance is running and was brought to the front.

    logging.info('Creating QApplication')
    app = QtWidgets.QApplication(sys.argv) # Main QApplication initialization
    app.setQuitOnLastWindowClosed(False)
    graceful_shutdown = False

    settings = Settings() # Initialize settings here, after QApplication
    logging.info('Settings loaded')

    # Set application icon (MOVED HERE)
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(__file__)
    icon_path = os.path.join(base_path, "mouse.ico")
    app_icon = QtGui.QIcon(icon_path)
    app.setWindowIcon(app_icon)

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



    # Watchdog shutdown flag
    shutdown_flag_id = "ScrollLockApp_ShutdownFlag"
    shutdown_flag_path = os.path.join(os.path.expanduser("~"), f".{shutdown_flag_id}.lock")

    # Clear any previous shutdown flag
    if os.path.exists(shutdown_flag_path):
        os.remove(shutdown_flag_path)





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

    hook = MouseHook(settings)
    logging.info('Mouse hook created')

    # Start hook thread
    t = threading.Thread(target=hook.start, daemon=True)
    t.start()
    logging.info('Hook thread started')

    # Tray icon + menu
    tray_icon = app_icon
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
    from app_context import AppContext
    app_context = AppContext(settings, hook, update_tray_icon, apply_global_font, tray, tray_icon)
    dlg = SettingsDialog(app_context, configure_startup)
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

    def exit_app():
        app.quit()

    act_help.triggered.connect(show_help_dialog)
    act_about.triggered.connect(show_about_dialog)
    act_exit.triggered.connect(exit_app)

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
        nonlocal graceful_shutdown
        graceful_shutdown = True
        logging.info('Application quitting')
        settings.sync()
        # The new SingleInstance class handles the mutex release automatically via its __del__ method
        # and OS-level mutex management. No manual cleanup is needed.

    app.aboutToQuit.connect(on_about_to_quit)

    logging.info('Starting event loop')
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()