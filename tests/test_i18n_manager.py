"""
Unit tests for the i18n manager.

This module contains comprehensive tests for the internationalization
and localization functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import sys
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.core_app.i18n_manager import (
    I18nManager, TranslationDomain, get_i18n_manager, set_i18n_manager, _, ngettext, pgettext
)
from src.eng_struct_tools.core_app.config import ConfigManager


class TestTranslationDomain(unittest.TestCase):
    """Test cases for TranslationDomain class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.domain_name = "test_domain"
        self.domain = TranslationDomain(self.domain_name, self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_domain_initialization(self):
        """Test domain initialization."""
        self.assertEqual(self.domain.domain_name, self.domain_name)
        self.assertEqual(self.domain.locale_dir, self.temp_dir)
        self.assertEqual(self.domain.fallback_locale, "en_US")
        self.assertEqual(self.domain.current_locale, "en_US")
        self.assertEqual(len(self.domain.translations), 0)
    
    def test_load_translation_file_not_found(self):
        """Test loading translation when file doesn't exist."""
        result = self.domain.load_translation("es_ES")
        self.assertFalse(result)
        self.assertNotIn("es_ES", self.domain.translations)
    
    def test_translate_without_translation(self):
        """Test translation when no translation is loaded."""
        message = "Hello, world!"
        result = self.domain.translate(message, "es_ES")
        self.assertEqual(result, message)  # Should return original message
    
    def test_ngettext_without_translation(self):
        """Test pluralization when no translation is loaded."""
        singular = "1 item"
        plural = "{count} items"
        
        result_singular = self.domain.ngettext(singular, plural, 1, "es_ES")
        self.assertEqual(result_singular, singular)
        
        result_plural = self.domain.ngettext(singular, plural, 5, "es_ES")
        self.assertEqual(result_plural, plural)


class TestI18nManager(unittest.TestCase):
    """Test cases for I18nManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_setting.return_value = None
        
        # Create a test locales directory
        self.locales_dir = self.temp_dir / "locales"
        self.locales_dir.mkdir()
        
        # Mock the core domain initialization
        with patch('src.eng_struct_tools.core_app.i18n_manager.Path') as mock_path:
            mock_path.return_value.parent.parent.parent.parent = self.temp_dir
            self.i18n_manager = I18nManager(self.config_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.i18n_manager.config_manager)
        self.assertEqual(self.i18n_manager.current_locale, "en_US")  # Default fallback
        self.assertIsNotNone(self.i18n_manager.current_babel_locale)
        self.assertIn("eng_struct_tools", self.i18n_manager.domains)
    
    def test_locale_detection(self):
        """Test locale detection."""
        # Test with user configuration
        self.config_manager.get_setting.return_value = "fr_FR"
        detected = self.i18n_manager._detect_locale()
        self.assertEqual(detected, "fr_FR")
        
        # Test fallback to system locale
        self.config_manager.get_setting.return_value = None
        with patch('locale.getdefaultlocale') as mock_locale:
            mock_locale.return_value = ("es_ES", "UTF-8")
            detected = self.i18n_manager._detect_locale()
            self.assertEqual(detected, "es_ES")
    
    def test_set_locale_valid(self):
        """Test setting a valid locale."""
        result = self.i18n_manager.set_locale("es_ES")
        self.assertTrue(result)
        self.assertEqual(self.i18n_manager.current_locale, "es_ES")
    
    def test_set_locale_invalid(self):
        """Test setting an invalid locale."""
        result = self.i18n_manager.set_locale("invalid_locale")
        self.assertFalse(result)
        self.assertEqual(self.i18n_manager.current_locale, "en_US")  # Should remain unchanged
    
    def test_register_domain(self):
        """Test registering a translation domain."""
        domain = TranslationDomain("test_plugin", self.temp_dir)
        self.i18n_manager.register_domain(domain)
        self.assertIn("test_plugin", self.i18n_manager.domains)
        self.assertEqual(self.i18n_manager.domains["test_plugin"], domain)
    
    def test_unregister_domain(self):
        """Test unregistering a translation domain."""
        domain = TranslationDomain("test_plugin", self.temp_dir)
        self.i18n_manager.register_domain(domain)
        self.assertIn("test_plugin", self.i18n_manager.domains)
        
        self.i18n_manager.unregister_domain("test_plugin")
        self.assertNotIn("test_plugin", self.i18n_manager.domains)
    
    def test_translate_unknown_domain(self):
        """Test translation with unknown domain."""
        message = "Test message"
        result = self.i18n_manager.translate(message, "unknown_domain")
        self.assertEqual(result, message)  # Should return original message
    
    def test_translate_known_domain(self):
        """Test translation with known domain."""
        domain = Mock(spec=TranslationDomain)
        domain.translate.return_value = "Translated message"
        self.i18n_manager.domains["test_domain"] = domain
        
        result = self.i18n_manager.translate("Test message", "test_domain")
        self.assertEqual(result, "Translated message")
        domain.translate.assert_called_once_with("Test message", self.i18n_manager.current_locale, None)
    
    def test_ngettext_known_domain(self):
        """Test pluralization with known domain."""
        domain = Mock(spec=TranslationDomain)
        domain.ngettext.return_value = "5 elementos"
        self.i18n_manager.domains["test_domain"] = domain
        
        result = self.i18n_manager.ngettext("1 item", "{count} items", 5, "test_domain")
        self.assertEqual(result, "5 elementos")
        domain.ngettext.assert_called_once_with("1 item", "{count} items", 5, self.i18n_manager.current_locale)
    
    def test_locale_observers(self):
        """Test locale change observers."""
        observer_called = False
        new_locale = None
        
        def test_observer(locale):
            nonlocal observer_called, new_locale
            observer_called = True
            new_locale = locale
        
        self.i18n_manager.add_locale_observer(test_observer)
        self.i18n_manager.set_locale("fr_FR")
        
        self.assertTrue(observer_called)
        self.assertEqual(new_locale, "fr_FR")
    
    def test_is_rtl_locale(self):
        """Test RTL locale detection."""
        # Test LTR locale
        self.i18n_manager.set_locale("en_US")
        self.assertFalse(self.i18n_manager.is_rtl_locale())
        
        # Test RTL locale
        self.i18n_manager.set_locale("ar_SA")
        self.assertTrue(self.i18n_manager.is_rtl_locale())
    
    def test_format_number(self):
        """Test number formatting."""
        # Test decimal formatting
        result = self.i18n_manager.format_number(1234.56, "decimal")
        self.assertIsInstance(result, str)
        
        # Test currency formatting
        result = self.i18n_manager.format_number(1234.56, "currency")
        self.assertIsInstance(result, str)
        
        # Test percent formatting
        result = self.i18n_manager.format_number(0.1234, "percent")
        self.assertIsInstance(result, str)
    
    def test_format_datetime(self):
        """Test datetime formatting."""
        from datetime import datetime
        dt = datetime(2024, 1, 15, 14, 30, 0)
        
        result = self.i18n_manager.format_datetime(dt, "medium")
        self.assertIsInstance(result, str)


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global i18n functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_manager = get_i18n_manager()
        self.mock_manager = Mock(spec=I18nManager)
        set_i18n_manager(self.mock_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        set_i18n_manager(self.original_manager)
    
    def test_underscore_function(self):
        """Test the _ (underscore) translation function."""
        self.mock_manager.translate.return_value = "Translated message"
        
        result = _("Test message")
        self.assertEqual(result, "Translated message")
        self.mock_manager.translate.assert_called_once_with("Test message", "eng_struct_tools")
    
    def test_underscore_function_no_manager(self):
        """Test _ function when no manager is set."""
        set_i18n_manager(None)
        
        result = _("Test message")
        self.assertEqual(result, "Test message")  # Should return original
    
    def test_ngettext_function(self):
        """Test the ngettext function."""
        self.mock_manager.ngettext.return_value = "5 elementos"
        
        result = ngettext("1 item", "{count} items", 5)
        self.assertEqual(result, "5 elementos")
        self.mock_manager.ngettext.assert_called_once_with("1 item", "{count} items", 5, "eng_struct_tools")
    
    def test_pgettext_function(self):
        """Test the pgettext function."""
        self.mock_manager.translate.return_value = "Archivo"
        
        result = pgettext("menu", "File")
        self.assertEqual(result, "Archivo")
        self.mock_manager.translate.assert_called_once_with("File", "eng_struct_tools", "menu")


if __name__ == "__main__":
    unittest.main()
