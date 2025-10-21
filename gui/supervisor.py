# supervisor.py
# Simple supervised launcher with exponential backoff and a hard restart cap.
from __future__ import annotations

import os
import subprocess
import sys
import time


def run_with_backoff(target_argv, max_restarts=5, base_delay=1.0, env=None):
    restarts = 0
    delay = base_delay

    while True:
        child_env = dict(os.environ)
        child_env["_MWF_SUPERVISED"] = "1"
        if env:
            child_env.update(env)

        proc = subprocess.Popen(target_argv, env=child_env)
        code = proc.wait()
        if code == 0:
            return 0

        restarts += 1
        if restarts > max_restarts:
            return code

        time.sleep(delay)
        delay = min(delay * 2.0, 30.0)


if __name__ == "__main__":
    if os.environ.get("_MWF_SUPERVISED") == "1":
        sys.exit(0)
    sys.exit(run_with_backoff([sys.executable, "-m", "MouseWheelFixer.main"]))
