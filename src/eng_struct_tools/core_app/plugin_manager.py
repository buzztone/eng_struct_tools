"""
Plugin manager for the Engineering Structural Tools application.

This module handles plugin discovery, loading, lifecycle management,
and provides the interface between plugins and the core application.
"""

import logging
import importlib
import importlib.metadata
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import traceback

from .plugin_base import PluginBase, PluginInfo, PluginStatus, HostAPI, MenuItem
from .config import ConfigManager


class PluginLoadError(Exception):
    """Exception raised when plugin loading fails."""

    pass


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.

    This class is responsible for:
    - Discovering plugins through entry points
    - Loading and initializing plugins
    - Managing plugin lifecycle (activate/deactivate)
    - Providing host API to plugins
    - Handling plugin errors and cleanup
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the plugin manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # Plugin storage
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.active_plugin: Optional[str] = None

        # Host API (will be set when main window is available)
        self.host_api: Optional[HostAPI] = None

        # Entry point group for plugin discovery
        self.entry_point_group = "eng_struct_tools.plugins"

        self.logger.info("Plugin manager initialized")

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins through entry points.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        try:
            # Get entry points for our plugin group
            entry_points = importlib.metadata.entry_points()

            if hasattr(entry_points, "select"):
                # Python 3.10+ style
                plugin_entries = entry_points.select(group=self.entry_point_group)
            else:
                # Python 3.9 style
                plugin_entries = entry_points.get(self.entry_point_group, [])

            for entry_point in plugin_entries:
                try:
                    plugin_name = entry_point.name
                    discovered.append(plugin_name)
                    self.logger.info(f"Discovered plugin: {plugin_name}")

                except Exception as e:
                    self.logger.error(
                        f"Error discovering plugin {entry_point.name}: {e}"
                    )

        except Exception as e:
            self.logger.error(f"Error during plugin discovery: {e}")

        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            True if plugin loaded successfully, False otherwise
        """
        if plugin_name in self.plugins:
            self.logger.warning(f"Plugin {plugin_name} is already loaded")
            return True

        try:
            self.logger.info(f"Loading plugin: {plugin_name}")

            # Get entry point
            entry_points = importlib.metadata.entry_points()

            if hasattr(entry_points, "select"):
                plugin_entries = entry_points.select(
                    group=self.entry_point_group, name=plugin_name
                )
                plugin_entries = list(plugin_entries)
            else:
                plugin_entries = entry_points.get(self.entry_point_group, [])
                plugin_entries = [ep for ep in plugin_entries if ep.name == plugin_name]

            if not plugin_entries:
                raise PluginLoadError(f"Plugin {plugin_name} not found in entry points")

            entry_point = plugin_entries[0]

            # Load plugin class
            plugin_class = entry_point.load()

            # Validate plugin class
            if not issubclass(plugin_class, PluginBase):
                raise PluginLoadError(
                    f"Plugin {plugin_name} does not inherit from PluginBase"
                )

            # Create plugin instance
            plugin_instance = plugin_class()

            # Get plugin info
            plugin_info = plugin_instance.get_plugin_info()
            plugin_info.status = PluginStatus.LOADING

            # Validate dependencies
            deps_valid, missing_deps = plugin_instance.validate_dependencies()
            if not deps_valid:
                raise PluginLoadError(
                    f"Missing dependencies: {', '.join(missing_deps)}"
                )

            # Initialize plugin if host API is available
            if self.host_api:
                if not plugin_instance.initialize(self.host_api):
                    raise PluginLoadError(f"Plugin {plugin_name} initialization failed")

            # Store plugin
            self.plugins[plugin_name] = plugin_instance
            plugin_info.status = PluginStatus.LOADED
            self.plugin_info[plugin_name] = plugin_info

            self.logger.info(f"Plugin {plugin_name} loaded successfully")
            return True

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_name}: {e}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())

            # Store error info
            if plugin_name not in self.plugin_info:
                self.plugin_info[plugin_name] = PluginInfo(
                    name=plugin_name,
                    version="unknown",
                    description="Failed to load",
                    author="unknown",
                    category="unknown",
                    dependencies=[],
                )

            self.plugin_info[plugin_name].status = PluginStatus.ERROR
            self.plugin_info[plugin_name].error_message = str(e)

            return False

    def load_plugins(self, main_window) -> None:
        """
        Load all discovered plugins.

        Args:
            main_window: Main application window for host API
        """
        # Create host API
        self.host_api = HostAPI(main_window, self.config_manager, self.logger)

        # Discover and load plugins
        discovered_plugins = self.discover_plugins()

        if not discovered_plugins:
            self.logger.warning("No plugins discovered")
            return

        loaded_count = 0
        for plugin_name in discovered_plugins:
            if self.load_plugin(plugin_name):
                loaded_count += 1
                self._register_plugin_ui(plugin_name, main_window)

        self.logger.info(f"Loaded {loaded_count}/{len(discovered_plugins)} plugins")

    def _register_plugin_ui(self, plugin_name: str, main_window) -> None:
        """
        Register plugin UI with the main window.

        Args:
            plugin_name: Name of the plugin
            main_window: Main application window
        """
        try:
            plugin = self.plugins[plugin_name]

            # Get menu items
            menu_items = plugin.get_menu_items()

            # Convert MenuItem objects to (name, callback) tuples
            menu_tuples = []
            for item in menu_items:
                # Create callback that activates plugin and calls original callback
                def create_callback(original_callback, p_name=plugin_name):
                    def callback():
                        self.activate_plugin(p_name)
                        original_callback()

                    return callback

                menu_tuples.append((item.name, create_callback(item.callback)))

            # Register with main window
            main_window.add_plugin_menu_items(plugin.get_tool_name(), menu_tuples)

        except Exception as e:
            self.logger.error(f"Failed to register UI for plugin {plugin_name}: {e}")

    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Activate a plugin.

        Args:
            plugin_name: Name of the plugin to activate

        Returns:
            True if plugin activated successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin {plugin_name} not loaded")
            return False

        try:
            # Deactivate current plugin if any
            if self.active_plugin and self.active_plugin != plugin_name:
                self.deactivate_plugin(self.active_plugin)

            plugin = self.plugins[plugin_name]

            # Create main widget if not already created
            if not plugin.main_widget:
                plugin._main_widget = plugin.create_main_widget()

            # Show plugin UI
            if self.host_api and plugin.main_widget:
                self.host_api.main_window.show_plugin_ui(plugin.main_widget)

            # Call plugin activation
            plugin.on_activate()

            # Update status
            self.plugin_info[plugin_name].status = PluginStatus.ACTIVE
            self.active_plugin = plugin_name

            self.logger.info(f"Plugin {plugin_name} activated")
            return True

        except Exception as e:
            self.logger.error(f"Failed to activate plugin {plugin_name}: {e}")
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_name: Name of the plugin to deactivate

        Returns:
            True if plugin deactivated successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            return True  # Already not active

        try:
            plugin = self.plugins[plugin_name]

            # Call plugin deactivation
            plugin.on_deactivate()

            # Update status
            self.plugin_info[plugin_name].status = PluginStatus.LOADED

            if self.active_plugin == plugin_name:
                self.active_plugin = None

            self.logger.info(f"Plugin {plugin_name} deactivated")
            return True

        except Exception as e:
            self.logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if plugin unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            return True  # Already not loaded

        try:
            # Deactivate first if active
            if self.active_plugin == plugin_name:
                self.deactivate_plugin(plugin_name)

            plugin = self.plugins[plugin_name]

            # Call plugin shutdown
            plugin.shutdown()

            # Remove from storage
            del self.plugins[plugin_name]
            self.plugin_info[plugin_name].status = PluginStatus.UNLOADED

            self.logger.info(f"Plugin {plugin_name} unloaded")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def shutdown_all_plugins(self) -> None:
        """Shutdown all loaded plugins."""
        self.logger.info("Shutting down all plugins...")

        # Deactivate active plugin
        if self.active_plugin:
            self.deactivate_plugin(self.active_plugin)

        # Unload all plugins
        plugin_names = list(self.plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)

        self.logger.info("All plugins shut down")

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Get information about a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginInfo object or None if plugin not found
        """
        return self.plugin_info.get(plugin_name)

    def get_all_plugin_info(self) -> Dict[str, PluginInfo]:
        """Get information about all plugins."""
        return self.plugin_info.copy()

    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names."""
        return list(self.plugins.keys())

    def get_active_plugin(self) -> Optional[str]:
        """Get the name of the currently active plugin."""
        return self.active_plugin

    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self.plugins

    def is_plugin_active(self, plugin_name: str) -> bool:
        """Check if a plugin is active."""
        return self.active_plugin == plugin_name

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin.

        Args:
            plugin_name: Name of the plugin to reload

        Returns:
            True if plugin reloaded successfully, False otherwise
        """
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)

        return self.load_plugin(plugin_name)

    def get_plugin_statistics(self) -> Dict[str, int]:
        """
        Get plugin statistics.

        Returns:
            Dictionary with plugin counts by status
        """
        stats = {
            "total": len(self.plugin_info),
            "loaded": 0,
            "active": 0,
            "error": 0,
            "disabled": 0,
        }

        for info in self.plugin_info.values():
            if info.status == PluginStatus.LOADED:
                stats["loaded"] += 1
            elif info.status == PluginStatus.ACTIVE:
                stats["active"] += 1
            elif info.status == PluginStatus.ERROR:
                stats["error"] += 1
            elif info.status == PluginStatus.DISABLED:
                stats["disabled"] += 1

        return stats
