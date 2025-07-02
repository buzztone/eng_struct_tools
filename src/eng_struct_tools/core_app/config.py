"""
Configuration management for the Engineering Structural Tools application.

This module provides centralized configuration management using QSettings
for persistent storage of application and plugin settings.
"""

import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path
import json

from PyQt6.QtCore import QSettings


class ConfigManager:
    """
    Manages application and plugin configuration settings.

    This class provides a centralized interface for storing and retrieving
    configuration settings using Qt's QSettings for persistence.
    """

    def __init__(
        self,
        organization: str = "Neil Murray",
        application: str = "Engineering Structural Tools",
    ):
        """
        Initialize the configuration manager.

        Args:
            organization: Organization name for settings storage
            application: Application name for settings storage
        """
        self.logger = logging.getLogger(__name__)

        # Initialize QSettings
        self.settings = QSettings(organization, application)

        # Default configuration values
        self.defaults = {
            # Application settings
            "app/theme": "default",
            "app/language": "en",
            "app/auto_save": True,
            "app/auto_save_interval": 300,  # seconds
            "app/recent_files_count": 10,
            # Window settings
            "window/geometry": None,
            "window/state": None,
            "window/maximized": False,
            # Units settings
            "units/length": "mm",
            "units/force": "N",
            "units/stress": "MPa",
            "units/moment": "N.mm",
            "units/temperature": "C",
            # IFC settings
            "ifc/default_schema": "IFC4",
            "ifc/precision": 6,
            "ifc/units_context": "metric",
            # Calculation settings
            "calc/precision": 3,
            "calc/safety_factors": {"concrete": 1.5, "steel": 1.15, "timber": 1.3},
            # Plugin settings
            "plugins/auto_load": True,
            "plugins/disabled": [],
            # Logging settings
            "logging/level": "INFO",
            "logging/file_enabled": True,
            "logging/console_enabled": True,
            "logging/max_file_size": 10485760,  # 10MB
            "logging/backup_count": 5,
            # Internationalization settings
            "i18n/locale": None,  # Auto-detect if None
            "i18n/fallback_locale": "en_US",
            "i18n/auto_detect": True,
            "i18n/date_format": "medium",
            "i18n/number_format": "decimal",
            "i18n/currency": "USD",
            "i18n/timezone": None,  # Auto-detect if None
        }

        self.logger.info("Configuration manager initialized")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting.

        Args:
            key: Setting key (can use '/' for nested keys)
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        try:
            # Check if we have a default for this key
            if default is None and key in self.defaults:
                default = self.defaults[key]

            # Get value from QSettings
            value = self.settings.value(key, default)

            # Handle special cases for type conversion
            if isinstance(default, bool) and isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            elif isinstance(default, int) and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    value = default
            elif isinstance(default, float) and isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    value = default
            elif isinstance(default, dict) and isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = default
            elif isinstance(default, list) and isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = default

            return value

        except Exception as e:
            self.logger.warning(f"Error getting setting '{key}': {e}")
            return default

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a configuration setting.

        Args:
            key: Setting key (can use '/' for nested keys)
            value: Setting value
        """
        try:
            # Convert complex types to JSON strings
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            self.settings.setValue(key, value)
            self.logger.debug(f"Set setting '{key}' = {value}")

        except Exception as e:
            self.logger.error(f"Error setting '{key}': {e}")

    def remove_setting(self, key: str) -> None:
        """
        Remove a configuration setting.

        Args:
            key: Setting key to remove
        """
        try:
            self.settings.remove(key)
            self.logger.debug(f"Removed setting '{key}'")
        except Exception as e:
            self.logger.error(f"Error removing setting '{key}': {e}")

    def has_setting(self, key: str) -> bool:
        """
        Check if a setting exists.

        Args:
            key: Setting key to check

        Returns:
            True if setting exists, False otherwise
        """
        return self.settings.contains(key)

    def get_all_settings(self, prefix: str = "") -> Dict[str, Any]:
        """
        Get all settings with optional prefix filter.

        Args:
            prefix: Optional prefix to filter settings

        Returns:
            Dictionary of settings
        """
        settings_dict = {}

        try:
            if prefix:
                self.settings.beginGroup(prefix)

            for key in self.settings.allKeys():
                full_key = f"{prefix}/{key}" if prefix else key
                settings_dict[full_key] = self.get_setting(full_key)

            if prefix:
                self.settings.endGroup()

        except Exception as e:
            self.logger.error(f"Error getting all settings: {e}")

        return settings_dict

    def reset_to_defaults(self, prefix: str = "") -> None:
        """
        Reset settings to defaults.

        Args:
            prefix: Optional prefix to reset only specific settings
        """
        try:
            if prefix:
                # Reset only settings with the given prefix
                for key in list(self.defaults.keys()):
                    if key.startswith(prefix):
                        self.set_setting(key, self.defaults[key])
            else:
                # Reset all settings
                self.settings.clear()
                for key, value in self.defaults.items():
                    self.set_setting(key, value)

            self.logger.info(f"Reset settings to defaults (prefix: '{prefix}')")

        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}")

    def save_settings(self) -> None:
        """Force save settings to disk."""
        try:
            self.settings.sync()
            self.logger.debug("Settings saved to disk")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def get_plugin_setting(
        self, plugin_name: str, key: str, default: Any = None
    ) -> Any:
        """
        Get a plugin-specific setting.

        Args:
            plugin_name: Name of the plugin
            key: Setting key
            default: Default value

        Returns:
            Setting value or default
        """
        plugin_key = f"plugins/{plugin_name}/{key}"
        return self.get_setting(plugin_key, default)

    def set_plugin_setting(self, plugin_name: str, key: str, value: Any) -> None:
        """
        Set a plugin-specific setting.

        Args:
            plugin_name: Name of the plugin
            key: Setting key
            value: Setting value
        """
        plugin_key = f"plugins/{plugin_name}/{key}"
        self.set_setting(plugin_key, value)

    def get_plugin_settings(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get all settings for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Dictionary of plugin settings
        """
        return self.get_all_settings(f"plugins/{plugin_name}")

    def export_settings(self, file_path: Union[str, Path]) -> bool:
        """
        Export settings to a JSON file.

        Args:
            file_path: Path to export file

        Returns:
            True if export successful, False otherwise
        """
        try:
            settings_dict = self.get_all_settings()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Settings exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: Union[str, Path]) -> bool:
        """
        Import settings from a JSON file.

        Args:
            file_path: Path to import file

        Returns:
            True if import successful, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                settings_dict = json.load(f)

            for key, value in settings_dict.items():
                self.set_setting(key, value)

            self.save_settings()
            self.logger.info(f"Settings imported from {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False

    def get_recent_files(self) -> list:
        """Get list of recent files."""
        return self.get_setting("app/recent_files", [])

    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the file
        """
        recent_files = self.get_recent_files()

        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)

        # Add to beginning
        recent_files.insert(0, file_path)

        # Limit list size
        max_count = self.get_setting("app/recent_files_count", 10)
        recent_files = recent_files[:max_count]

        self.set_setting("app/recent_files", recent_files)

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.set_setting("app/recent_files", [])
