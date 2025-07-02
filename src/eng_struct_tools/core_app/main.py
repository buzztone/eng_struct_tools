"""
Main entry point for the Engineering Structural Tools application.

This module contains the main application class and entry point for the
plugin-based structural engineering design tools.
"""

import sys
import logging
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QStatusBar,
    QStackedWidget,
    QLabel,
    QMessageBox,
    QProgressBar,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QPixmap

from .plugin_manager import PluginManager
from .config import ConfigManager
from .i18n_manager import I18nManager, set_i18n_manager, _
from .l10n_utils import LocalizationUtils, set_l10n_utils
from ..shared_libs.common_ui_widgets import StatusWidget
from ..shared_libs.unit_converter import UnitConverter


class MainWindow(QMainWindow):
    """
    Main application window for the Engineering Structural Tools.

    This window provides the main interface including menu bar, central widget area,
    and status bar. It manages plugin UIs and provides a unified user experience.
    """

    # Signals
    plugin_selected = pyqtSignal(str)  # Emitted when a plugin is selected
    status_message = pyqtSignal(str, int)  # Message, timeout in ms

    def __init__(
        self,
        config_manager: ConfigManager,
        plugin_manager: PluginManager,
        i18n_manager: I18nManager,
        l10n_utils: LocalizationUtils,
    ):
        """
        Initialize the main window.

        Args:
            config_manager: Configuration manager instance
            plugin_manager: Plugin manager instance
            i18n_manager: Internationalization manager instance
            l10n_utils: Localization utilities instance
        """
        super().__init__()
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        self.i18n_manager = i18n_manager
        self.l10n_utils = l10n_utils
        self.logger = logging.getLogger(__name__)

        # Set up locale change observer
        self.i18n_manager.add_locale_observer(self._on_locale_changed)

        # Initialize UI components
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._connect_signals()

        # Load window settings
        self._load_window_settings()

        self.logger.info("Main window initialized successfully")

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Set window properties
        self.setWindowTitle(_("Engineering Structural Tools"))
        self.setMinimumSize(1200, 800)

        # Create central widget with stacked layout for plugin UIs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create splitter for resizable areas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel for navigation/tools (future enhancement)
        # For now, just use the menu bar for navigation

        # Central area for plugin UIs
        self.central_stack = QStackedWidget()
        splitter.addWidget(self.central_stack)

        # Welcome widget (shown when no plugin is active)
        self._create_welcome_widget()

        # Set splitter proportions
        splitter.setSizes([200, 1000])  # Left panel: 200px, Central: 1000px

    def _create_welcome_widget(self) -> None:
        """Create the welcome widget shown when no plugin is active."""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Welcome message
        welcome_label = QLabel(_("Welcome to Engineering Structural Tools"))
        welcome_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        # Instructions
        instructions = QLabel(
            _(
                "Select a tool from the menu above to begin structural analysis and design."
            )
        )
        instructions.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                margin: 10px;
            }
        """
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)

        # Add to stack
        self.central_stack.addWidget(welcome_widget)
        self.central_stack.setCurrentWidget(welcome_widget)

    def _setup_menu_bar(self) -> None:
        """Set up the menu bar with plugin entries."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(_("&File"))

        # New project action
        new_action = QAction(_("&New Project"), self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip(_("Create a new project"))
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        # Open project action
        open_action = QAction(_("&Open Project"), self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip(_("Open an existing project"))
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction(_("E&xit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip(_("Exit application"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu (will be populated by plugins)
        self.tools_menu = menubar.addMenu(_("&Tools"))

        # Settings menu
        settings_menu = menubar.addMenu(_("&Settings"))

        # Language submenu
        language_menu = settings_menu.addMenu(_("&Language"))
        self._setup_language_menu(language_menu)

        # Help menu
        help_menu = menubar.addMenu(_("&Help"))

        about_action = QAction(_("&About"), self)
        about_action.setStatusTip(_("About this application"))
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_language_menu(self, language_menu) -> None:
        """Set up the language selection menu."""
        available_locales = self.i18n_manager.get_available_locales()
        current_locale = self.i18n_manager.get_locale()

        for locale_code in available_locales:
            try:
                from babel import Locale

                locale_obj = Locale.parse(locale_code)
                display_name = locale_obj.display_name
            except:
                display_name = locale_code

            action = QAction(display_name, self)
            action.setCheckable(True)
            action.setChecked(locale_code == current_locale)
            action.triggered.connect(
                lambda checked, lc=locale_code: self._change_language(lc)
            )
            language_menu.addAction(action)

    def _change_language(self, locale_code: str) -> None:
        """Change the application language."""
        if self.i18n_manager.set_locale(locale_code):
            # Language change will trigger _on_locale_changed
            pass
        else:
            QMessageBox.warning(
                self,
                _("Language Change"),
                _("Failed to change language to {locale}").format(locale=locale_code),
            )

    def _on_locale_changed(self, new_locale: str) -> None:
        """Handle locale change events."""
        # Update UI text direction if needed
        if self.i18n_manager.is_rtl_locale():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Refresh UI elements that need retranslation
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        """Retranslate UI elements after locale change."""
        # Update window title
        self.setWindowTitle(_("Engineering Structural Tools"))

        # Update status bar
        if hasattr(self, "status_label"):
            self.status_label.setText(_("Ready"))

        # Note: Menu items and other dynamic content would need more complex handling
        # For now, we'll recommend restarting the application for full language change

    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        self.status_bar = self.statusBar()

        # Status message label
        self.status_label = QLabel(_("Ready"))
        self.status_bar.addWidget(self.status_label)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Plugin status widget
        self.plugin_status = StatusWidget()
        self.status_bar.addPermanentWidget(self.plugin_status)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.status_message.connect(self._update_status_message)
        self.plugin_selected.connect(self._on_plugin_selected)

    def _load_window_settings(self) -> None:
        """Load window settings from configuration."""
        try:
            # Load window geometry and state
            geometry = self.config_manager.get_setting("window/geometry")
            if geometry:
                self.restoreGeometry(geometry)

            state = self.config_manager.get_setting("window/state")
            if state:
                self.restoreState(state)

        except Exception as e:
            self.logger.warning(f"Failed to load window settings: {e}")

    def _save_window_settings(self) -> None:
        """Save window settings to configuration."""
        try:
            self.config_manager.set_setting("window/geometry", self.saveGeometry())
            self.config_manager.set_setting("window/state", self.saveState())
        except Exception as e:
            self.logger.warning(f"Failed to save window settings: {e}")

    def add_plugin_menu_items(self, plugin_name: str, menu_items: list) -> None:
        """
        Add menu items for a plugin.

        Args:
            plugin_name: Name of the plugin
            menu_items: List of (name, callback) tuples
        """
        if not menu_items:
            return

        # Create submenu for plugin if multiple items
        if len(menu_items) > 1:
            plugin_menu = self.tools_menu.addMenu(plugin_name)
            for item_name, callback in menu_items:
                action = QAction(item_name, self)
                action.triggered.connect(callback)
                plugin_menu.addAction(action)
        else:
            # Single item - add directly to tools menu
            item_name, callback = menu_items[0]
            action = QAction(f"{plugin_name} - {item_name}", self)
            action.triggered.connect(callback)
            self.tools_menu.addAction(action)

    def show_plugin_ui(self, plugin_widget: QWidget) -> None:
        """
        Show a plugin's UI in the central area.

        Args:
            plugin_widget: The plugin's main widget
        """
        # Add widget to stack if not already present
        if plugin_widget not in [
            self.central_stack.widget(i) for i in range(self.central_stack.count())
        ]:
            self.central_stack.addWidget(plugin_widget)

        # Switch to plugin widget
        self.central_stack.setCurrentWidget(plugin_widget)
        self.logger.info(f"Switched to plugin UI: {plugin_widget.__class__.__name__}")

    def show_progress(self, show: bool = True) -> None:
        """Show or hide the progress bar."""
        self.progress_bar.setVisible(show)

    def set_progress(self, value: int) -> None:
        """Set progress bar value (0-100)."""
        self.progress_bar.setValue(value)

    def _update_status_message(self, message: str, timeout: int = 0) -> None:
        """Update status bar message."""
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText("Ready"))

    def _on_plugin_selected(self, plugin_name: str) -> None:
        """Handle plugin selection."""
        self.status_message.emit(f"Loading {plugin_name}...", 2000)

    def _new_project(self) -> None:
        """Handle new project action."""
        # TODO: Implement new project functionality
        self.status_message.emit("New project functionality not yet implemented", 3000)

    def _open_project(self) -> None:
        """Handle open project action."""
        # TODO: Implement open project functionality
        self.status_message.emit("Open project functionality not yet implemented", 3000)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Engineering Structural Tools",
            """
            <h3>Engineering Structural Tools v0.1.0</h3>
            <p>A modular plugin-based application for structural engineering
            analysis and design.</p>
            <p>Built with PyQt6 and Python.</p>
            <p>© 2024 Neil Murray</p>
            """,
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self._save_window_settings()

        # Notify plugin manager of shutdown
        try:
            self.plugin_manager.shutdown_all_plugins()
        except Exception as e:
            self.logger.error(f"Error during plugin shutdown: {e}")

        event.accept()


class EngStructToolsApp:
    """
    Main application class for Engineering Structural Tools.

    This class manages the overall application lifecycle, including
    initialization, plugin loading, and cleanup.
    """

    def __init__(self):
        """Initialize the application."""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.config_manager: Optional[ConfigManager] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Set up application logging."""
        # Create logs directory if it doesn't exist
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "eng_struct_tools.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized")
        return logger

    def initialize(self) -> bool:
        """
        Initialize the application components.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Engineering Structural Tools...")

            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Engineering Structural Tools")
            self.app.setApplicationVersion("0.1.0")
            self.app.setOrganizationName("Neil Murray")

            # Initialize configuration manager
            self.config_manager = ConfigManager()

            # Initialize i18n system
            self.i18n_manager = I18nManager(self.config_manager)
            set_i18n_manager(self.i18n_manager)

            # Initialize localization utilities
            unit_converter = UnitConverter()  # Create unit converter instance
            self.l10n_utils = LocalizationUtils(unit_converter)
            set_l10n_utils(self.l10n_utils)

            # Initialize plugin manager
            self.plugin_manager = PluginManager(self.config_manager)

            # Create main window
            self.main_window = MainWindow(
                self.config_manager,
                self.plugin_manager,
                self.i18n_manager,
                self.l10n_utils,
            )

            # Load plugins
            self.plugin_manager.load_plugins(self.main_window)

            self.logger.info("Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code
        """
        if not self.initialize():
            return 1

        try:
            # Show main window
            self.main_window.show()

            # Start event loop
            return self.app.exec()

        except Exception as e:
            self.logger.error(f"Application error: {e}")
            return 1

    def shutdown(self) -> None:
        """Clean shutdown of the application."""
        self.logger.info("Shutting down application...")

        if self.plugin_manager:
            self.plugin_manager.shutdown_all_plugins()

        if self.config_manager:
            self.config_manager.save_settings()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Application exit code
    """
    app = EngStructToolsApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
