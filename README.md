# MouseWheelFixer

A lightweight but powerful Windows utility to prevent accidental mouse wheel scrolling and "jitter."

An executable version, `wheel.exe`, is available in the main folder.

**Important Note:** Because the application uses a low-level mouse hook to function, some antivirus software may flag it as a potential threat. This is a false positive. Please allow the executable to run or add an exclusion for it in your antivirus settings.

---

## The Problem: Annoying Mouse Wheel Jitter

Have you ever been scrolling through a long document or webpage, only to have the page "jump" back up slightly when you stop?

This often happens with sensitive or free-spinning mouse wheels. When the wheel comes to a halt, it can physically "bounce" or "jitter," sending one or more scroll events in the opposite direction. This tiny, accidental input is enough to make your view jump, which can be distracting and frustrating.

## How It Works: The Solution

MouseWheelFixer solves this by intelligently monitoring mouse wheel activity and blocking these accidental "jitter" events.

It works through a simple but effective workflow:

1.  **Low-Level Mouse Hook**: The application registers a `WH_MOUSE_LL` hook, a feature in Windows that allows it to monitor all low-level mouse events system-wide, specifically looking for `WM_MOUSEWHEEL` messages.

2.  **Establishing a Direction**: When you scroll, the application notes the direction (up or down) and starts a very short timer, known as the **Block Interval**.

3.  **Blocking the Jitter**:
    *   If you continue scrolling in the **same direction**, the timer simply resets, and scrolling proceeds as normal.
    *   If a scroll event in the **opposite direction** occurs within the block interval, the application assumes it's an accidental jitter and **blocks it**. This is the core of the fix.

4.  **Allowing Deliberate Changes**: What if you *meant* to change direction quickly? That's what the **Direction Change Threshold** is for. This setting defines how many consecutive opposite-direction events are needed to override the block. If you scroll aggressively enough in the new direction, the application recognizes it as a deliberate change, establishes a new scrolling direction, and lets the events pass through.

5.  **Visual Feedback**: Whenever a scroll event is blocked, a small "🚫" indicator flashes near your cursor, giving you clear, immediate feedback that the application is working.

This entire process happens instantly and uses minimal system resources, resulting in a much smoother and more predictable scrolling experience.

## Features

*   **Customizable Blocking Logic**: Fine-tune the `Block Interval` and `Direction Change Threshold` to match your mouse's sensitivity and your personal preference.
*   **Application Blacklist**: Disable scroll blocking for specific applications (e.g., games, design software) where you need raw, unfiltered mouse input.
*   **Per-Application Profiles**: Define unique `Interval` and `Threshold` settings for different applications.
*   **Start on Boot**: Set the application to launch automatically with Windows. When enabled, a watchdog process ensures the app remains running.
*   **System Tray Control**: The application runs quietly in the system tray. Right-click the icon to access settings, toggle blocking, or exit.
*   **Visual Indicator**: A customizable overlay that shows you when a scroll event has been blocked.

## Command-line Arguments

*   `--no-watchdog`: Run the application without the watchdog process. This is useful for development and debugging, as it prevents the application from automatically restarting.