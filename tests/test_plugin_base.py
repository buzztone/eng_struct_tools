"""
Unit tests for the plugin base classes.

This module contains tests for the plugin architecture including
base classes, interfaces, and plugin information structures.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.eng_struct_tools.core_app.plugin_base import (
    PluginBase, StructuralAnalysisPlugin, DesignPlugin,
    PluginInfo, PluginStatus, MenuItem, HostAPI
)


class TestPluginInfo:
    """Test cases for PluginInfo dataclass."""
    
    def test_initialization(self):
        """Test PluginInfo initialization."""
        info = PluginInfo(
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="Testing",
            dependencies=["numpy"]
        )
        
        assert info.name == "Test Plugin"
        assert info.version == "1.0.0"
        assert info.description == "A test plugin"
        assert info.author == "Test Author"
        assert info.category == "Testing"
        assert info.dependencies == ["numpy"]
        assert info.status == PluginStatus.UNLOADED
        assert info.error_message is None
    
    def test_default_values(self):
        """Test PluginInfo default values."""
        info = PluginInfo(
            name="Test",
            version="1.0",
            description="Test",
            author="Author",
            category="Category",
            dependencies=[]
        )
        
        assert info.status == PluginStatus.UNLOADED
        assert info.error_message is None


class TestMenuItem:
    """Test cases for MenuItem dataclass."""
    
    def test_initialization(self):
        """Test MenuItem initialization."""
        callback = lambda: None
        item = MenuItem(
            name="Test Item",
            callback=callback,
            tooltip="Test tooltip",
            shortcut="Ctrl+T",
            enabled=True
        )
        
        assert item.name == "Test Item"
        assert item.callback == callback
        assert item.tooltip == "Test tooltip"
        assert item.shortcut == "Ctrl+T"
        assert item.enabled is True
    
    def test_default_values(self):
        """Test MenuItem default values."""
        callback = lambda: None
        item = MenuItem(name="Test", callback=callback)
        
        assert item.icon is None
        assert item.tooltip is None
        assert item.shortcut is None
        assert item.enabled is True


class TestHostAPI:
    """Test cases for HostAPI class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_main_window = Mock()
        self.mock_config_manager = Mock()
        self.mock_logger = Mock()
        
        self.host_api = HostAPI(
            self.mock_main_window,
            self.mock_config_manager,
            self.mock_logger
        )
    
    def test_initialization(self):
        """Test HostAPI initialization."""
        assert self.host_api.main_window == self.mock_main_window
        assert self.host_api.config_manager == self.mock_config_manager
        assert self.host_api.logger == self.mock_logger
    
    def test_show_status_message(self):
        """Test showing status message."""
        self.host_api.show_status_message("Test message", 1000)
        self.mock_main_window.status_message.emit.assert_called_once_with("Test message", 1000)
    
    def test_show_progress(self):
        """Test showing progress."""
        self.host_api.show_progress(True)
        self.mock_main_window.show_progress.assert_called_once_with(True)
    
    def test_set_progress(self):
        """Test setting progress value."""
        self.host_api.set_progress(50)
        self.mock_main_window.set_progress.assert_called_once_with(50)
    
    def test_get_setting(self):
        """Test getting configuration setting."""
        self.mock_config_manager.get_setting.return_value = "test_value"
        result = self.host_api.get_setting("test_key", "default")
        
        self.mock_config_manager.get_setting.assert_called_once_with("test_key", "default")
        assert result == "test_value"
    
    def test_set_setting(self):
        """Test setting configuration value."""
        self.host_api.set_setting("test_key", "test_value")
        self.mock_config_manager.set_setting.assert_called_once_with("test_key", "test_value")
    
    def test_logging_methods(self):
        """Test logging methods."""
        self.host_api.log_info("Info message")
        self.mock_logger.info.assert_called_once_with("Info message")
        
        self.host_api.log_warning("Warning message")
        self.mock_logger.warning.assert_called_once_with("Warning message")
        
        self.host_api.log_error("Error message")
        self.mock_logger.error.assert_called_once_with("Error message")


class ConcretePlugin(PluginBase):
    """Concrete implementation of PluginBase for testing."""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Test Plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category="Testing",
            dependencies=[]
        )
    
    def initialize(self, host_api: HostAPI) -> bool:
        self.host_api = host_api
        self._is_initialized = True
        return True
    
    def get_menu_items(self) -> List[MenuItem]:
        return [MenuItem(name="Test Action", callback=lambda: None)]
    
    def create_main_widget(self, parent=None):
        return Mock()


class TestPluginBase:
    """Test cases for PluginBase abstract class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = ConcretePlugin()
        self.mock_host_api = Mock(spec=HostAPI)
    
    def test_initialization(self):
        """Test plugin initialization."""
        assert self.plugin.host_api is None
        assert self.plugin.plugin_info is None
        assert not self.plugin.is_initialized
        assert self.plugin.main_widget is None
    
    def test_initialize(self):
        """Test plugin initialization with host API."""
        result = self.plugin.initialize(self.mock_host_api)
        
        assert result is True
        assert self.plugin.host_api == self.mock_host_api
        assert self.plugin.is_initialized
    
    def test_get_tool_name(self):
        """Test getting tool name."""
        name = self.plugin.get_tool_name()
        assert name == "Test Plugin"
    
    def test_get_tool_icon(self):
        """Test getting tool icon (default implementation)."""
        icon = self.plugin.get_tool_icon()
        assert icon is None
    
    def test_validate_dependencies(self):
        """Test dependency validation."""
        # Test with no dependencies
        is_valid, missing = self.plugin.validate_dependencies()
        assert is_valid is True
        assert missing == []
        
        # Test with missing dependency
        plugin_info = self.plugin.get_plugin_info()
        plugin_info.dependencies = ["nonexistent_module"]
        self.plugin.plugin_info = plugin_info
        
        is_valid, missing = self.plugin.validate_dependencies()
        assert is_valid is False
        assert "nonexistent_module" in missing
    
    def test_lifecycle_methods(self):
        """Test plugin lifecycle methods."""
        # These should not raise exceptions
        self.plugin.on_activate()
        self.plugin.on_deactivate()
        self.plugin.shutdown()
    
    def test_configuration_schema(self):
        """Test configuration schema (default implementation)."""
        schema = self.plugin.get_configuration_schema()
        assert schema is None


class ConcreteAnalysisPlugin(StructuralAnalysisPlugin):
    """Concrete implementation of StructuralAnalysisPlugin for testing."""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Analysis Plugin",
            version="1.0.0",
            description="Analysis plugin",
            author="Test Author",
            category="Analysis",
            dependencies=[]
        )
    
    def initialize(self, host_api: HostAPI) -> bool:
        return True
    
    def get_menu_items(self) -> List[MenuItem]:
        return []
    
    def create_main_widget(self, parent=None):
        return Mock()
    
    def run_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "test_result"}
    
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        return True, []


class TestStructuralAnalysisPlugin:
    """Test cases for StructuralAnalysisPlugin class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = ConcreteAnalysisPlugin()
    
    def test_initialization(self):
        """Test analysis plugin initialization."""
        assert self.plugin.analysis_results is None
    
    def test_run_analysis(self):
        """Test running analysis."""
        input_data = {"param1": "value1"}
        results = self.plugin.run_analysis(input_data)
        
        assert results == {"result": "test_result"}
    
    def test_get_analysis_results(self):
        """Test getting analysis results."""
        # Initially None
        assert self.plugin.get_analysis_results() is None
        
        # Set results
        test_results = {"test": "data"}
        self.plugin.analysis_results = test_results
        assert self.plugin.get_analysis_results() == test_results
    
    def test_clear_results(self):
        """Test clearing analysis results."""
        self.plugin.analysis_results = {"test": "data"}
        self.plugin.clear_results()
        assert self.plugin.analysis_results is None


class ConcreteDesignPlugin(DesignPlugin):
    """Concrete implementation of DesignPlugin for testing."""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Design Plugin",
            version="1.0.0",
            description="Design plugin",
            author="Test Author",
            category="Design",
            dependencies=[]
        )
    
    def initialize(self, host_api: HostAPI) -> bool:
        return True
    
    def get_menu_items(self) -> List[MenuItem]:
        return []
    
    def create_main_widget(self, parent=None):
        return Mock()
    
    def run_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"design_result": "test_design"}
    
    def check_design_codes(self) -> List[str]:
        return ["ACI 318", "Eurocode 2"]


class TestDesignPlugin:
    """Test cases for DesignPlugin class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = ConcreteDesignPlugin()
    
    def test_initialization(self):
        """Test design plugin initialization."""
        assert self.plugin.design_results is None
    
    def test_run_design(self):
        """Test running design."""
        input_data = {"param1": "value1"}
        results = self.plugin.run_design(input_data)
        
        assert results == {"design_result": "test_design"}
    
    def test_check_design_codes(self):
        """Test checking design codes."""
        codes = self.plugin.check_design_codes()
        assert "ACI 318" in codes
        assert "Eurocode 2" in codes
    
    def test_get_design_results(self):
        """Test getting design results."""
        # Initially None
        assert self.plugin.get_design_results() is None
        
        # Set results
        test_results = {"design": "data"}
        self.plugin.design_results = test_results
        assert self.plugin.get_design_results() == test_results
    
    def test_clear_results(self):
        """Test clearing design results."""
        self.plugin.design_results = {"design": "data"}
        self.plugin.clear_results()
        assert self.plugin.design_results is None
