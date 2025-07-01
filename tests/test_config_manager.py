"""
Unit tests for the ConfigManager class.

This module contains tests for configuration management functionality
including setting/getting values, validation, and persistence.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.eng_struct_tools.core_app.config import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Use a temporary organization/application name for testing
        self.config_manager = ConfigManager("TestOrg", "TestApp")
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Clear all settings
        self.config_manager.settings.clear()
    
    def test_initialization(self):
        """Test ConfigManager initialization."""
        assert self.config_manager is not None
        assert hasattr(self.config_manager, 'settings')
        assert hasattr(self.config_manager, 'defaults')
        assert len(self.config_manager.defaults) > 0
    
    def test_get_setting_with_default(self):
        """Test getting a setting that uses default value."""
        # Test getting a setting that should use default
        theme = self.config_manager.get_setting("app/theme")
        assert theme == "default"  # From defaults
        
        # Test getting a setting with explicit default
        custom_value = self.config_manager.get_setting("nonexistent/key", "custom_default")
        assert custom_value == "custom_default"
    
    def test_set_and_get_setting(self):
        """Test setting and getting configuration values."""
        # Test string value
        self.config_manager.set_setting("test/string", "test_value")
        assert self.config_manager.get_setting("test/string") == "test_value"
        
        # Test integer value
        self.config_manager.set_setting("test/integer", 42)
        assert self.config_manager.get_setting("test/integer") == 42
        
        # Test float value
        self.config_manager.set_setting("test/float", 3.14)
        assert self.config_manager.get_setting("test/float") == 3.14
        
        # Test boolean value
        self.config_manager.set_setting("test/boolean", True)
        assert self.config_manager.get_setting("test/boolean") is True
    
    def test_complex_data_types(self):
        """Test setting and getting complex data types (dict, list)."""
        # Test dictionary
        test_dict = {"key1": "value1", "key2": 42, "key3": True}
        self.config_manager.set_setting("test/dict", test_dict)
        retrieved_dict = self.config_manager.get_setting("test/dict")
        assert retrieved_dict == test_dict
        
        # Test list
        test_list = ["item1", "item2", 123, True]
        self.config_manager.set_setting("test/list", test_list)
        retrieved_list = self.config_manager.get_setting("test/list")
        assert retrieved_list == test_list
    
    def test_has_setting(self):
        """Test checking if a setting exists."""
        # Setting should not exist initially
        assert not self.config_manager.has_setting("test/exists")
        
        # Set a value
        self.config_manager.set_setting("test/exists", "value")
        
        # Setting should now exist
        assert self.config_manager.has_setting("test/exists")
    
    def test_remove_setting(self):
        """Test removing a setting."""
        # Set a value
        self.config_manager.set_setting("test/remove", "value")
        assert self.config_manager.has_setting("test/remove")
        
        # Remove the setting
        self.config_manager.remove_setting("test/remove")
        assert not self.config_manager.has_setting("test/remove")
    
    def test_get_all_settings(self):
        """Test getting all settings."""
        # Set some test values
        self.config_manager.set_setting("test/value1", "data1")
        self.config_manager.set_setting("test/value2", "data2")
        self.config_manager.set_setting("other/value", "data3")
        
        # Get all settings
        all_settings = self.config_manager.get_all_settings()
        assert isinstance(all_settings, dict)
        assert "test/value1" in all_settings
        assert "test/value2" in all_settings
        assert "other/value" in all_settings
        
        # Get settings with prefix
        test_settings = self.config_manager.get_all_settings("test")
        assert len(test_settings) >= 2
    
    def test_plugin_settings(self):
        """Test plugin-specific setting methods."""
        plugin_name = "test_plugin"
        
        # Set plugin setting
        self.config_manager.set_plugin_setting(plugin_name, "setting1", "value1")
        
        # Get plugin setting
        value = self.config_manager.get_plugin_setting(plugin_name, "setting1")
        assert value == "value1"
        
        # Get plugin setting with default
        default_value = self.config_manager.get_plugin_setting(plugin_name, "nonexistent", "default")
        assert default_value == "default"
        
        # Get all plugin settings
        self.config_manager.set_plugin_setting(plugin_name, "setting2", "value2")
        plugin_settings = self.config_manager.get_plugin_settings(plugin_name)
        assert len(plugin_settings) >= 2
    
    def test_recent_files(self):
        """Test recent files functionality."""
        # Initially should be empty
        recent_files = self.config_manager.get_recent_files()
        assert isinstance(recent_files, list)
        
        # Add some files
        self.config_manager.add_recent_file("/path/to/file1.ifc")
        self.config_manager.add_recent_file("/path/to/file2.ifc")
        
        recent_files = self.config_manager.get_recent_files()
        assert len(recent_files) == 2
        assert recent_files[0] == "/path/to/file2.ifc"  # Most recent first
        assert recent_files[1] == "/path/to/file1.ifc"
        
        # Add duplicate (should move to front)
        self.config_manager.add_recent_file("/path/to/file1.ifc")
        recent_files = self.config_manager.get_recent_files()
        assert len(recent_files) == 2
        assert recent_files[0] == "/path/to/file1.ifc"
        
        # Clear recent files
        self.config_manager.clear_recent_files()
        recent_files = self.config_manager.get_recent_files()
        assert len(recent_files) == 0
    
    def test_export_import_settings(self):
        """Test exporting and importing settings."""
        # Set some test settings
        self.config_manager.set_setting("test/export1", "value1")
        self.config_manager.set_setting("test/export2", {"key": "value"})
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Export settings
            success = self.config_manager.export_settings(temp_path)
            assert success
            
            # Verify file exists and contains data
            assert Path(temp_path).exists()
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            assert "test/export1" in exported_data
            assert "test/export2" in exported_data
            
            # Clear settings and import
            self.config_manager.remove_setting("test/export1")
            self.config_manager.remove_setting("test/export2")
            
            success = self.config_manager.import_settings(temp_path)
            assert success
            
            # Verify settings were imported
            assert self.config_manager.get_setting("test/export1") == "value1"
            assert self.config_manager.get_setting("test/export2") == {"key": "value"}
            
        finally:
            # Clean up temporary file
            Path(temp_path).unlink(missing_ok=True)
    
    def test_reset_to_defaults(self):
        """Test resetting settings to defaults."""
        # Set some custom values
        self.config_manager.set_setting("app/theme", "custom_theme")
        self.config_manager.set_setting("test/custom", "custom_value")
        
        # Reset app settings to defaults
        self.config_manager.reset_to_defaults("app")
        
        # App theme should be reset to default
        assert self.config_manager.get_setting("app/theme") == "default"
        
        # Custom setting should still exist
        assert self.config_manager.get_setting("test/custom") == "custom_value"
        
        # Reset all settings
        self.config_manager.reset_to_defaults()
        
        # All defaults should be restored
        assert self.config_manager.get_setting("app/theme") == "default"
        assert self.config_manager.get_setting("units/length") == "mm"
    
    def test_error_handling(self):
        """Test error handling in configuration operations."""
        # Test export to invalid path
        success = self.config_manager.export_settings("/invalid/path/file.json")
        assert not success
        
        # Test import from non-existent file
        success = self.config_manager.import_settings("/non/existent/file.json")
        assert not success
    
    @patch('src.eng_struct_tools.core_app.config.QSettings')
    def test_qsettings_integration(self, mock_qsettings):
        """Test integration with QSettings."""
        # Create a mock QSettings instance
        mock_settings = Mock()
        mock_qsettings.return_value = mock_settings
        
        # Create config manager (will use mocked QSettings)
        config_manager = ConfigManager("TestOrg", "TestApp")
        
        # Test that QSettings was called with correct parameters
        mock_qsettings.assert_called_once_with("TestOrg", "TestApp")
        
        # Test setting a value
        config_manager.set_setting("test/key", "test_value")
        mock_settings.setValue.assert_called_with("test/key", "test_value")
        
        # Test getting a value
        mock_settings.value.return_value = "test_value"
        value = config_manager.get_setting("test/key")
        mock_settings.value.assert_called()
        assert value == "test_value"
