"""
Plugin base classes and interfaces for the Engineering Structural Tools.

This module defines the abstract base classes and interfaces that all plugins
must implement to integrate with the core application.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon


class PluginStatus(Enum):
    """Plugin status enumeration."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Plugin information container."""
    name: str
    version: str
    description: str
    author: str
    category: str
    dependencies: List[str]
    status: PluginStatus = PluginStatus.UNLOADED
    error_message: Optional[str] = None


@dataclass
class MenuItem:
    """Menu item definition for plugins."""
    name: str
    callback: callable
    icon: Optional[QIcon] = None
    tooltip: Optional[str] = None
    shortcut: Optional[str] = None
    enabled: bool = True


class HostAPI:
    """
    Host API interface provided to plugins.
    
    This class provides plugins with access to core application services
    such as logging, configuration, UI integration, and data exchange.
    """
    
    def __init__(self, main_window, config_manager, logger):
        """
        Initialize the host API.
        
        Args:
            main_window: Reference to the main application window
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.config_manager = config_manager
        self.logger = logger
    
    def show_status_message(self, message: str, timeout: int = 0) -> None:
        """
        Show a status message in the main window.
        
        Args:
            message: Message to display
            timeout: Timeout in milliseconds (0 = no timeout)
        """
        self.main_window.status_message.emit(message, timeout)
    
    def show_progress(self, show: bool = True) -> None:
        """Show or hide the progress bar."""
        self.main_window.show_progress(show)
    
    def set_progress(self, value: int) -> None:
        """Set progress bar value (0-100)."""
        self.main_window.set_progress(value)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return self.config_manager.get_setting(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        self.config_manager.set_setting(key, value)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)


class PluginBase(ABC):
    """
    Abstract base class for all plugins.
    
    All plugins must inherit from this class and implement the required methods.
    This ensures a consistent interface for plugin discovery, loading, and execution.
    """
    
    def __init__(self):
        """Initialize the plugin."""
        self.host_api: Optional[HostAPI] = None
        self.plugin_info: Optional[PluginInfo] = None
        self._is_initialized = False
        self._main_widget: Optional[QWidget] = None
    
    @abstractmethod
    def get_plugin_info(self) -> PluginInfo:
        """
        Get plugin information.
        
        Returns:
            PluginInfo object containing plugin metadata
        """
        pass
    
    @abstractmethod
    def initialize(self, host_api: HostAPI) -> bool:
        """
        Initialize the plugin with host API access.
        
        This method is called when the plugin is loaded. It should perform
        any necessary initialization and setup.
        
        Args:
            host_api: Host API interface for accessing core services
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_menu_items(self) -> List[MenuItem]:
        """
        Get menu items for this plugin.
        
        Returns:
            List of MenuItem objects defining the plugin's menu entries
        """
        pass
    
    @abstractmethod
    def create_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the main widget for this plugin.
        
        This method should create and return the main UI widget for the plugin.
        The widget will be displayed in the main application's central area.
        
        Args:
            parent: Parent widget (optional)
            
        Returns:
            Main plugin widget
        """
        pass
    
    def get_tool_name(self) -> str:
        """
        Get the human-readable tool name.
        
        Returns:
            Tool name string
        """
        info = self.get_plugin_info()
        return info.name
    
    def get_tool_icon(self) -> Optional[QIcon]:
        """
        Get the tool icon.
        
        Returns:
            QIcon object or None if no icon available
        """
        return None
    
    def shutdown(self) -> None:
        """
        Shutdown the plugin.
        
        This method is called when the plugin is being unloaded or the
        application is shutting down. Override to perform cleanup.
        """
        pass
    
    def on_activate(self) -> None:
        """
        Called when the plugin becomes active.
        
        Override this method to perform actions when the plugin's UI
        becomes visible or active.
        """
        pass
    
    def on_deactivate(self) -> None:
        """
        Called when the plugin becomes inactive.
        
        Override this method to perform actions when the plugin's UI
        is hidden or becomes inactive.
        """
        pass
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dictionary defining the plugin's configuration schema,
            or None if no configuration is needed
        """
        return None
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate plugin dependencies.
        
        Returns:
            Tuple of (success, missing_dependencies)
        """
        info = self.get_plugin_info()
        missing = []
        
        for dep in info.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._is_initialized
    
    @property
    def main_widget(self) -> Optional[QWidget]:
        """Get the main widget instance."""
        return self._main_widget


class StructuralAnalysisPlugin(PluginBase):
    """
    Base class for structural analysis plugins.
    
    This class provides common functionality for plugins that perform
    structural analysis calculations.
    """
    
    def __init__(self):
        """Initialize the structural analysis plugin."""
        super().__init__()
        self.analysis_results: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def run_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the structural analysis.
        
        Args:
            input_data: Input parameters for the analysis
            
        Returns:
            Analysis results dictionary
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate input data for the analysis.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest analysis results."""
        return self.analysis_results
    
    def clear_results(self) -> None:
        """Clear analysis results."""
        self.analysis_results = None


class DesignPlugin(PluginBase):
    """
    Base class for design plugins.
    
    This class provides common functionality for plugins that perform
    structural design calculations.
    """
    
    def __init__(self):
        """Initialize the design plugin."""
        super().__init__()
        self.design_results: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def run_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the structural design.
        
        Args:
            input_data: Input parameters for the design
            
        Returns:
            Design results dictionary
        """
        pass
    
    @abstractmethod
    def check_design_codes(self) -> List[str]:
        """
        Get list of supported design codes.
        
        Returns:
            List of design code names/standards
        """
        pass
    
    def get_design_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest design results."""
        return self.design_results
    
    def clear_results(self) -> None:
        """Clear design results."""
        self.design_results = None
