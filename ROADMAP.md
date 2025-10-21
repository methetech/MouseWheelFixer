# Project Roadmap

This document outlines the future direction and potential features for WheelScrollFixer. It's a living document intended to guide development and inspire contributions. If you're looking for a way to contribute, picking up an item from this list is a great place to start!

## Near-Term Goals (Quality of Life & UX)

These are smaller, achievable enhancements focused on improving the user experience and providing more immediate feedback.

*   [ ] **Dynamic Tray Icon Tooltip**: Update the system tray icon's tooltip to show the current status (e.g., "Enabled - Global Profile", "Disabled", "Enabled - chrome.exe Profile").
*   [ ] **Dynamic Tray Icon Visuals**: Change the tray icon's appearance (e.g., gray it out) when scroll blocking is disabled.
*   [ ] **"Live Stats" View**: Add a new tab or window that shows real-time debug information, such as:
    *   The currently detected foreground application.
    *   The active profile (Global or app-specific).
    *   Live counters for blocked scroll events.
*   [ ] **UI Theming**: Add a simple Light/Dark mode toggle to respect user system settings.
*   [ ] **Configuration Import/Export**: Allow users to back up their complete settings (global, blacklist, profiles) to a single file and restore them.

## Mid-Term Goals (Core Feature Enhancements)

These features expand the core functionality of the application, turning it into a more comprehensive mouse utility.

*   [ ] **Advanced Scrolling Control**:
    *   **Scroll Reversal**: Add a per-profile option to reverse the scroll direction ("Natural Scrolling").
    *   **Scroll Acceleration**: Allow users to define a custom scroll acceleration curve.
*   [ ] **Horizontal Scrolling Support**: Extend the hook and blocking logic to the mouse tilt-wheel (`WM_MOUSEHWHEEL`).
*   [ ] **Enhanced Profile Detection**: Allow profiles to be triggered not just by `exe` name, but also by window title, for more granular control (e.g., different settings for different websites within a browser).
*   [ ] **Localization (i18n)**: Refactor the UI strings into a format that allows for community-contributed translations into other languages.

## Long-Term & Ambitious Goals (Major New Functionality)

These are transformative features that would significantly expand the scope of the application, potentially turning it into an open-source competitor to commercial power-user tools.

*   [ ] **Mouse Button Remapping**:
    *   Allow users to re-assign the function of any mouse button (e.g., make a side button act as a middle-click).
    *   This would be configurable on a per-profile basis.
*   [ ] **Simple Macro Support**:
    *   Allow a mouse button to trigger a keyboard shortcut (e.g., `Ctrl+W` to close a tab) or a short sequence of key presses.
*   [ ] **Mouse Gestures**:
    *   Implement a system to detect gestures, such as holding a button while moving the mouse or scrolling the wheel.
    *   *Example*: Hold Right-Click + Scroll to adjust system volume.
    *   *Example*: Hold Side Button + Move Mouse Left/Right to switch virtual desktops.
*   [ ] **Plugin Architecture**:
    *   This is the ultimate goal for extensibility. Refactor the core application to allow new functionality (like gestures or macros) to be added via plugins. This would create a powerful framework for community contributions.

## Project & Distribution

Improvements related to how the application is built, packaged, and updated.

*   [ ] **Automatic Update Checker**: Implement a feature that periodically checks the GitHub Releases page for a new version and notifies the user.

---

Have an idea that's not on this list? Feel free to open an issue to discuss it!