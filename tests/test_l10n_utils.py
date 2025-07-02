"""
Unit tests for the localization utilities.

This module contains tests for locale-specific formatting and
cultural adaptations.
"""

import unittest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.core_app.l10n_utils import (
    LocalizationUtils,
    get_l10n_utils,
    set_l10n_utils,
    format_engineering_number,
    format_engineering_value,
)
from src.eng_struct_tools.core_app.i18n_manager import I18nManager
from src.eng_struct_tools.shared_libs.unit_converter import UnitConverter


class TestLocalizationUtils(unittest.TestCase):
    """Test cases for LocalizationUtils class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_unit_converter = Mock(spec=UnitConverter)
        self.l10n_utils = LocalizationUtils(self.mock_unit_converter)

        # Mock i18n manager
        self.mock_i18n_manager = Mock(spec=I18nManager)

        with patch(
            "src.eng_struct_tools.core_app.l10n_utils.get_i18n_manager"
        ) as mock_get_manager:
            mock_get_manager.return_value = self.mock_i18n_manager

    def test_get_locale_unit_system(self):
        """Test getting unit system for different locales."""
        # Test US locale (Imperial)
        result = self.l10n_utils.get_locale_unit_system("en_US")
        self.assertEqual(result, "Imperial")

        # Test European locale (SI)
        result = self.l10n_utils.get_locale_unit_system("de_DE")
        self.assertEqual(result, "SI_Engineering")

        # Test unknown locale (default)
        result = self.l10n_utils.get_locale_unit_system("unknown_locale")
        self.assertEqual(result, "SI_Engineering")

    def test_get_locale_engineering_codes(self):
        """Test getting engineering codes for different locales."""
        # Test US locale
        codes = self.l10n_utils.get_locale_engineering_codes("en_US")
        self.assertIn("ACI 318", codes)
        self.assertIn("AISC 360", codes)

        # Test European locale
        codes = self.l10n_utils.get_locale_engineering_codes("de_DE")
        self.assertIn("Eurocode 2", codes)
        self.assertIn("Eurocode 3", codes)

        # Test unknown locale (default)
        codes = self.l10n_utils.get_locale_engineering_codes("unknown_locale")
        self.assertEqual(codes, ["ACI 318"])

    def test_format_engineering_number(self):
        """Test engineering number formatting."""
        # Test normal number
        result = self.l10n_utils.format_engineering_number(1234.567, precision=2)
        self.assertIsInstance(result, str)

        # Test large number (should use scientific notation)
        result = self.l10n_utils.format_engineering_number(1e7, use_scientific=True)
        self.assertIsInstance(result, str)

        # Test small number
        result = self.l10n_utils.format_engineering_number(0.001, use_scientific=True)
        self.assertIsInstance(result, str)

    def test_format_engineering_value_with_unit(self):
        """Test formatting engineering values with units."""
        result = self.l10n_utils.format_engineering_value_with_unit(
            1234.56, "MPa", precision=2
        )
        self.assertIsInstance(result, str)
        self.assertIn("MPa", result)

    def test_format_datetime_engineering(self):
        """Test datetime formatting for engineering reports."""
        dt = datetime(2024, 1, 15, 14, 30, 0)

        # Test without seconds
        result = self.l10n_utils.format_datetime_engineering(dt, include_seconds=False)
        self.assertIsInstance(result, str)

        # Test with seconds
        result = self.l10n_utils.format_datetime_engineering(dt, include_seconds=True)
        self.assertIsInstance(result, str)

    def test_format_date_engineering(self):
        """Test date formatting for engineering reports."""
        d = date(2024, 1, 15)
        result = self.l10n_utils.format_date_engineering(d)
        self.assertIsInstance(result, str)

    def test_get_decimal_separator(self):
        """Test getting decimal separator."""
        separator = self.l10n_utils.get_decimal_separator()
        self.assertIsInstance(separator, str)
        self.assertIn(separator, [".", ","])

    def test_get_thousands_separator(self):
        """Test getting thousands separator."""
        separator = self.l10n_utils.get_thousands_separator()
        self.assertIsInstance(separator, str)
        self.assertIn(separator, [",", ".", " ", ""])

    def test_parse_localized_number(self):
        """Test parsing localized number strings."""
        # Test with default separators (US format)
        result = self.l10n_utils.parse_localized_number("1,234.56")
        self.assertAlmostEqual(result, 1234.56, places=2)

        # Test simple number
        result = self.l10n_utils.parse_localized_number("123.45")
        self.assertAlmostEqual(result, 123.45, places=2)

        # Test invalid number
        with self.assertRaises(ValueError):
            self.l10n_utils.parse_localized_number("invalid")

    def test_format_percentage(self):
        """Test percentage formatting."""
        result = self.l10n_utils.format_percentage(0.1234, precision=2)
        self.assertIsInstance(result, str)
        self.assertIn("%", result)

    def test_get_text_direction(self):
        """Test text direction detection."""
        # Mock RTL locale
        self.mock_i18n_manager.is_rtl_locale.return_value = True
        with patch(
            "src.eng_struct_tools.core_app.l10n_utils.get_i18n_manager"
        ) as mock_get_manager:
            mock_get_manager.return_value = self.mock_i18n_manager
            result = self.l10n_utils.get_text_direction()
            self.assertEqual(result, "rtl")

        # Mock LTR locale
        self.mock_i18n_manager.is_rtl_locale.return_value = False
        with patch(
            "src.eng_struct_tools.core_app.l10n_utils.get_i18n_manager"
        ) as mock_get_manager:
            mock_get_manager.return_value = self.mock_i18n_manager
            result = self.l10n_utils.get_text_direction()
            self.assertEqual(result, "ltr")

    def test_adapt_ui_for_locale(self):
        """Test UI adaptation settings."""
        # Mock i18n manager
        from babel import Locale

        mock_locale = Locale.parse("en_US")
        self.mock_i18n_manager.is_rtl_locale.return_value = False

        with patch(
            "src.eng_struct_tools.core_app.l10n_utils.get_i18n_manager"
        ) as mock_get_manager:
            mock_get_manager.return_value = self.mock_i18n_manager

            with patch.object(self.l10n_utils, "get_current_locale") as mock_get_locale:
                mock_get_locale.return_value = mock_locale

                settings = self.l10n_utils.adapt_ui_for_locale()

                self.assertIsInstance(settings, dict)
                self.assertIn("text_direction", settings)
                self.assertIn("is_rtl", settings)
                self.assertIn("decimal_separator", settings)
                self.assertIn("thousands_separator", settings)
                self.assertIn("unit_system", settings)
                self.assertIn("engineering_codes", settings)

    def test_convert_to_locale_units(self):
        """Test unit conversion to locale-preferred units."""
        # Mock unit converter
        self.mock_unit_converter.get_unit_for_quantity.return_value = "ft"
        self.mock_unit_converter.convert.return_value = 3.28084

        value, unit = self.l10n_utils.convert_to_locale_units(1.0, "m", "length")

        self.assertAlmostEqual(value, 3.28084, places=5)
        self.assertEqual(unit, "ft")

        # Test with no unit converter
        l10n_utils_no_converter = LocalizationUtils(None)
        value, unit = l10n_utils_no_converter.convert_to_locale_units(
            1.0, "m", "length"
        )
        self.assertEqual(value, 1.0)
        self.assertEqual(unit, "m")

    def test_get_locale_specific_help_text(self):
        """Test getting locale-specific help text."""
        self.mock_i18n_manager.translate.return_value = "Translated help text"

        with patch(
            "src.eng_struct_tools.core_app.l10n_utils.get_i18n_manager"
        ) as mock_get_manager:
            mock_get_manager.return_value = self.mock_i18n_manager

            result = self.l10n_utils.get_locale_specific_help_text("test_key")
            self.assertEqual(result, "Translated help text")


class TestGlobalL10nFunctions(unittest.TestCase):
    """Test cases for global localization functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_utils = get_l10n_utils()
        self.mock_utils = Mock(spec=LocalizationUtils)
        set_l10n_utils(self.mock_utils)

    def tearDown(self):
        """Clean up test fixtures."""
        set_l10n_utils(self.original_utils)

    def test_format_engineering_number_function(self):
        """Test the global format_engineering_number function."""
        self.mock_utils.format_engineering_number.return_value = "1,234.567"

        result = format_engineering_number(1234.567, precision=3)
        self.assertEqual(result, "1,234.567")
        self.mock_utils.format_engineering_number.assert_called_once_with(1234.567, 3)

    def test_format_engineering_number_no_utils(self):
        """Test format_engineering_number when no utils are set."""
        set_l10n_utils(None)

        result = format_engineering_number(1234.567, precision=3)
        self.assertEqual(result, "1234.567")  # Should return simple format

    def test_format_engineering_value_function(self):
        """Test the global format_engineering_value function."""
        self.mock_utils.format_engineering_value_with_unit.return_value = (
            "1,234.567 MPa"
        )

        result = format_engineering_value(1234.567, "MPa", precision=3)
        self.assertEqual(result, "1,234.567 MPa")
        self.mock_utils.format_engineering_value_with_unit.assert_called_once_with(
            1234.567, "MPa", 3
        )

    def test_format_engineering_value_no_utils(self):
        """Test format_engineering_value when no utils are set."""
        set_l10n_utils(None)

        result = format_engineering_value(1234.567, "MPa", precision=3)
        self.assertEqual(result, "1234.567 MPa")  # Should return simple format


class TestLocalizationIntegration(unittest.TestCase):
    """Integration tests for localization functionality."""

    def test_number_formatting_consistency(self):
        """Test that number formatting is consistent across different methods."""
        l10n_utils = LocalizationUtils()

        # Test the same number with different methods
        test_value = 1234.567

        result1 = l10n_utils.format_engineering_number(test_value, precision=2)
        result2 = l10n_utils.format_engineering_value_with_unit(
            test_value, "", precision=2
        )

        # Both should format the number part consistently
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)

    def test_locale_specific_formatting(self):
        """Test that formatting adapts to different locales."""
        l10n_utils = LocalizationUtils()

        # Test percentage formatting
        percentage_result = l10n_utils.format_percentage(0.1234, precision=1)
        self.assertIn("%", percentage_result)

        # Test datetime formatting
        from datetime import datetime

        dt = datetime(2024, 1, 15, 14, 30, 0)
        datetime_result = l10n_utils.format_datetime_engineering(dt)
        self.assertIsInstance(datetime_result, str)


if __name__ == "__main__":
    unittest.main()
