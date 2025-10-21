# single_instance.py
# Robust Windows single-instance guard using a named mutex.
# Automatically released by the OS on crash/exit (no stale files).
from __future__ import annotations

import atexit

try:
    import win32api
    import win32con
    import win32event
except Exception as e:
    raise RuntimeError("This module requires Windows and pywin32 installed.") from e

MUTEX_NAME = r"Global\{A7B7A1E8-6AB9-4E93-8F2A-5F9CD9D1D3C1}_WheelScrollFixer"


class SingleInstanceError(RuntimeError):
    pass


class SingleInstance:
    def __init__(self, name: str = MUTEX_NAME):
        self.name = name
        self.handle = None
        self._acquire()
        atexit.register(self._release)

    def _acquire(self):
        self.handle = win32event.CreateMutex(None, True, self.name)
        # If already existed, GetLastError is ERROR_ALREADY_EXISTS
        if win32api.GetLastError() == win32con.ERROR_ALREADY_EXISTS:
            try:
                win32api.CloseHandle(self.handle)
            finally:
                self.handle = None
            raise SingleInstanceError("Another instance is already running.")

    def _release(self):
        try:
            if self.handle:
                win32event.ReleaseMutex(self.handle)
                win32api.CloseHandle(self.handle)
                self.handle = None
        except Exception:
            # Best-effort cleanup
            pass
