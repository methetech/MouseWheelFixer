# main.py
# Entry point that composes SingleInstance + Supervisor.
from __future__ import annotations

import os
import sys

from .single_instance import SingleInstance, SingleInstanceError


def _run():
    # Acquire the single-instance guard first
    try:
        _ = SingleInstance()
    except SingleInstanceError:
        print("MouseWheelFixer is already running.")
        return 0  # exit 0 so supervisor won't relaunch

    # Start the real app
    from .wheel_entry import run_app
    return run_app()


if __name__ == "__main__":
    if os.environ.get("_MWF_SUPERVISED") != "1":
        # Start under supervisor if not already marked
        from .supervisor import run_with_backoff
        sys.exit(run_with_backoff([sys.executable, "-m", "MouseWheelFixer.main"]))
    else:
        sys.exit(_run())
