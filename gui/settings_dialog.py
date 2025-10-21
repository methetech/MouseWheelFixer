"""Settings dialog for the WheelScrollFixer application."""
import os
from PyQt5 import QtWidgets, QtGui, QtCore
import utils
from .app_profile_dialog import AppProfileDialog
from .help_dialog import HelpDialog
from .about_dialog import AboutDialog

class SettingsDialog(QtWidgets.QDialog):
    """The main settings dialog for the application."""
    def __init__(self, app_context, configure_startup):
        super().__init__()
        self.app_context = app_context
        self.settings = app_context.settings
        self.hook = app_context.hook
        self.update_tray_icon_callback = app_context.update_tray_icon_callback
        self.update_font_callback = app_context.update_font_callback
        self.tray = app_context.tray
        

        self._init_ui(configure_startup)

    def _init_ui(self, configure_startup):
        """Initializes the user interface."""
        self.setWindowTitle('Scroll Lock Settings')
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "mouse.ico")))

        self._create_widgets()
        self._create_layouts()
        self._connect_signals(configure_startup)

    def _create_widgets(self):
        """Creates the widgets for the dialog."""
        self._create_menu_bar()
        self._create_blocking_logic_widgets()
        self._create_app_control_widgets()
        self._create_general_settings_widgets()

    def _create_menu_bar(self):
        """Creates the menu bar for the dialog."""
        self.menu_bar = QtWidgets.QMenuBar(self)
        help_menu = self.menu_bar.addMenu("&Help")
        act_about = help_menu.addAction("&About")
        act_documentation = help_menu.addAction("&Website")
        act_help_content = help_menu.addAction("Help &Content")
        act_whats_this = help_menu.addAction("What's &This?")
        act_whats_this.setShortcut(QtGui.QKeySequence("Shift+F1"))
        act_whats_this.triggered.connect(QtWidgets.QWhatsThis.enterWhatsThisMode)

        act_about.triggered.connect(self.show_about_dialog)
        act_documentation.triggered.connect(self.open_website)
        act_help_content.triggered.connect(self.show_help_dialog)

    def _create_blocking_logic_widgets(self):
        """Creates the widgets for the blocking logic settings."""
        self.interval_spin = QtWidgets.QDoubleSpinBox()
        self.interval_spin.setRange(0.05, 5.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(self.settings.get_interval())
        self.interval_spin.setToolTip(
            'The time interval (in seconds) during which rapid scroll direction changes will be blocked. '
            'Prevents accidental scrolling.'
        )
        self.interval_spin.setWhatsThis(
            'This setting controls the time window (in seconds) for blocking rapid changes in scroll direction. '
            'If you scroll in one direction, and then quickly scroll in the opposite direction within this interval, '
            'the second scroll event will be ignored. This helps prevent "jittery" or accidental scrolling.'
        )

        self.direction_change_threshold_spin = QtWidgets.QSpinBox()
        self.direction_change_threshold_spin.setRange(1, 10)
        self.direction_change_threshold_spin.setValue(self.settings.get_direction_change_threshold())
        self.direction_change_threshold_spin.setToolTip(
            'The number of consecutive opposite scroll events required to re-establish a new scroll direction '
            'within the block interval.'
        )
        self.direction_change_threshold_spin.setWhatsThis(
            'The number of consecutive opposite scroll events required to "break" the current blocking and '
            'establish a new scroll direction within the block interval. This allows for deliberate, '
            'quick changes in scroll direction if you scroll aggressively enough.'
        )

    def _create_app_control_widgets(self):
        """Creates the widgets for the application control settings."""
        self.bl_list = QtWidgets.QListWidget()
        self.bl_list.addItems(self.settings.get_blacklist())
        self.bl_list.setToolTip(
            'List of application executable names (e.g., chrome.exe) where scroll blocking will be disabled.'
        )
        self.bl_list.setWhatsThis(
            'This list displays application executable names (e.g., chrome.exe, notepad.exe) for which '
            'the scroll blocking functionality will be completely disabled. This is useful for applications '
            'where you need precise or unrestricted scrolling.'
        )

        self.bl_add_current_btn = QtWidgets.QPushButton('Add Current App')
        self.bl_add_current_btn.setToolTip("Add the foreground process.")
        self.bl_add_current_btn.setWhatsThis(
            'Click to add the currently focused application\'s executable name to the blacklist so scrolling '
            'is not blocked in that app.'
        )

        self.bl_remove_btn = QtWidgets.QPushButton("Remove Selected")
        self.bl_remove_btn.setToolTip("Remove selected blacklist entries.")
        self.bl_remove_btn.setWhatsThis(
            'Removes the selected application(s) from the blacklist, re-enabling scroll blocking for them.'
        )

        self.bl_clear_btn = QtWidgets.QPushButton("Clear All")
        self.bl_clear_btn.setToolTip("Clear blacklist.")
        self.bl_clear_btn.setWhatsThis(
            'Clears the entire blacklist. Scroll blocking will apply to all apps unless added again.'
        )

    def _create_general_settings_widgets(self):
        """Creates the widgets for the general settings."""
        self.start_cb = QtWidgets.QCheckBox("Start on boot")
        self.start_cb.setChecked(self.settings.get_startup())
        self.start_cb.setToolTip('If checked, the application will start automatically when Windows boots.')
        self.start_cb.setWhatsThis(
            'If checked, the main application and its child watchdog process will start automatically '
            'when Windows boots. This ensures the scroll blocking functionality is always active.'
        )

        self.enabled_cb = QtWidgets.QCheckBox('Enable Scroll Blocking')
        self.enabled_cb.setChecked(self.settings.get_enabled())
        self.enabled_cb.setToolTip('Master switch to enable or disable the scroll blocking functionality.')
        self.enabled_cb.setWhatsThis(
            'This is a master switch to globally enable or disable the scroll blocking functionality. '
            'When unchecked, no scroll events will be blocked, regardless of other settings.'
        )

        self.font_size_spin = QtWidgets.QDoubleSpinBox()
        self.font_size_spin.setRange(8.0, 24.0) # Reasonable font size range
        self.font_size_spin.setSingleStep(0.5)
        self.font_size_spin.setValue(self.settings.get_font_size())
        self.font_size_spin.setToolTip('Adjust the global font size for the application UI.')
        self.font_size_spin.setWhatsThis(
            'Adjust the global font size for the application user interface. This affects the size of text '
            'and elements within the application windows.'
        )

        self.save_btn = QtWidgets.QPushButton('Save')
        self.save_btn.setToolTip("Save all settings.")
        self.save_btn.setWhatsThis('Saves all changes to persistent settings, applies them immediately to the running hook, and updates the tray UI as needed.')

    def _create_layouts(self):
        """Creates the layouts for the dialog."""
        self._create_blocking_logic_layout()
        self._create_app_control_layout()
        self._create_general_settings_layout()
        self._create_app_profiles_layout()
        self._create_main_layout()

    def _create_blocking_logic_layout(self):
        """Creates the layout for the blocking logic settings."""
        blocking_group = QtWidgets.QGroupBox("Blocking Logic")
        blocking_group.setWhatsThis('Parameters that control how scroll blocking behaves.')
        blocking_layout = QtWidgets.QFormLayout()
        blocking_layout.addRow("Block interval (s):", self.interval_spin)
        blocking_layout.addRow("Direction change threshold:", self.direction_change_threshold_spin)
        blocking_group.setLayout(blocking_layout)
        self.blocking_group = blocking_group

    def _create_app_control_layout(self):
        """Creates the layout for the application control settings."""
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
        self.app_control_group = app_control_group

    def _create_general_settings_layout(self):
        """Creates the layout for the general settings."""
        general_settings_group = QtWidgets.QGroupBox("General Settings")
        general_settings_group.setWhatsThis('Startup behavior, master enable, and UI font size.')
        general_settings_layout = QtWidgets.QFormLayout()
        general_settings_layout.addRow(self.start_cb)
        general_settings_layout.addRow(self.enabled_cb)
        general_settings_layout.addRow("Font size (pt):", self.font_size_spin)



        general_settings_group.setLayout(general_settings_layout)
        self.general_settings_group = general_settings_group

    def _create_app_profiles_layout(self):
        """Creates the layout for the application profiles settings."""
        app_profiles_group = QtWidgets.QGroupBox("Application Profiles")
        app_profiles_group.setWhatsThis(
            'Define custom scroll blocking settings for specific applications.'
        )
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
        self.app_profiles_group = app_profiles_group

    def _create_main_layout(self):
        """Creates the main layout for the dialog."""
        form = QtWidgets.QFormLayout(self)
        form.setMenuBar(self.menu_bar)
        form.addRow(self.blocking_group)
        form.addRow(self.app_control_group)
        form.addRow(self.app_profiles_group)
        form.addRow(self.general_settings_group)
        form.addRow(self.save_btn)

    def _connect_signals(self, configure_startup):
        """Connects the signals for the dialog."""
        self.save_btn.clicked.connect(lambda: self.save(configure_startup))
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
            "WheelScrollFixer",
            "Application minimized to tray. Click the icon to restore.",
            self.app_context.icon,
            2000 # 2 seconds
        )

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.isMinimized():
                # Let the window minimize to the taskbar normally
                pass
        super().changeEvent(event)

    def refresh_app_profiles_list(self):
        self.app_profiles_list.clear()
        for app_name, profile in self.settings.get_app_profiles().items():
            interval = profile.get('interval', self.settings.get_interval())
            threshold = profile.get('threshold', self.settings.get_direction_change_threshold())
            self.app_profiles_list.addItem(
                f"{app_name}: Interval={interval:.2f}s, Threshold={threshold}"
            )

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
            current_threshold=profile_data.get(
                'threshold', self.settings.get_direction_change_threshold()
            ),
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



    def show_help_dialog(self):
        HelpDialog(self).exec_()

    def show_about_dialog(self):
        AboutDialog(self).exec_()

    def open_website(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://en.MetheTech.com"))

    def add_current_app_to_blacklist(self):
        # Hide briefly so the dialog isn't the foreground window
        self.hide()
        QtCore.QTimer.singleShot(120, self._get_and_add_foreground_app)

    def _get_and_add_foreground_app(self):
        proc_name = utils.get_foreground_process_name()
        existing = [self.bl_list.item(i).text() for i in range(self.bl_list.count())]
        if proc_name and proc_name not in existing:
            self.bl_list.addItem(proc_name)
        self.show()

    def remove_selected_from_blacklist(self):
        for item in self.bl_list.selectedItems():
            self.bl_list.takeItem(self.bl_list.row(item))

    def clear_blacklist(self):
        self.bl_list.clear()



    def save(self, configure_startup):
        """Saves all settings and applies them live."""
        self.settings.set_interval(self.interval_spin.value())
        bl = [self.bl_list.item(i).text() for i in range(self.bl_list.count())]
        self.settings.set_blacklist(bl)
        self.settings.set_startup(self.start_cb.isChecked())
        configure_startup(self.start_cb.isChecked())
        
        self.settings.set_enabled(self.enabled_cb.isChecked())
        self.settings.set_direction_change_threshold(self.direction_change_threshold_spin.value())
        self.settings.set_font_size(self.font_size_spin.value())


        # Explicitly sync settings to INI file
        self.settings.sync()

        # Apply settings live
        self.hook.reload_settings(self.update_tray_icon_callback, self.update_font_callback)
        self.apply_settings()
        QtWidgets.QMessageBox.information(self, "Saved", "Settings saved.")
