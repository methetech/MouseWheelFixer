# utils.py
import psutil
import win32gui
import win32process

def get_foreground_process_name():
    """Gets the name of the foreground process."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
