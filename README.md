# MouseWheelFixer

An executable version of this software, `wheel.exe`, is available in the main folder. It includes the `mouse.ico` as its icon.

**Important Note:** Due to the nature of how Python scripts are converted into executables, `wheel.exe` may be flagged by antivirus software (such as Windows Defender) as a potential threat. This is often a false positive. If you encounter such a warning, please allow the executable to run or add an exclusion for it in your antivirus settings to use the software.

---

# Scroll Lock Application — Help

This app reduces accidental wheel scrolls by blocking rapid direction changes inside a short time window.

## Blocking Logic

*   **Block interval (s):** The time window during which opposite-direction wheel events are considered jitter and can be blocked.
*   **Direction change threshold:** Count of consecutive opposite events required within the interval to accept a deliberate change.

## Application Control

*   **Blacklist:** Executable names (e.g. `chrome.exe`) where blocking is disabled.
*   **Add Current App:** Quickly adds the foreground process to the blacklist.
*   **Start on boot:** Launches the app at Windows startup (with a watchdog).
*   **Enable Scroll Blocking:** Master switch.

## Visual Feedback

A small “🚫” flashes near your cursor when an event is blocked.

## Watchdog

If "Start on boot" is enabled, a detached watchdog will relaunch the app if it dies, ensuring continuity. This can be disabled for development purposes by using the `--no-watchdog` command-line flag.

## Command-line Arguments

*   `--no-watchdog`: Run the application without the watchdog process. This is useful for development and debugging, as it prevents the application from automatically restarting.
