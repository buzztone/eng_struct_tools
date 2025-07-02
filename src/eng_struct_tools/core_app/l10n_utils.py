"""
Localization utilities for the Engineering Structural Tools application.

This module provides utilities for locale-specific formatting, cultural
adaptations, and integration with the unit conversion system.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, time
from decimal import Decimal

from babel import Locale
from babel.dates import format_datetime, format_date, format_time
from babel.numbers import format_decimal, format_currency, format_percent, format_scientific
from babel.units import format_unit

from .i18n_manager import get_i18n_manager
from ..shared_libs.unit_converter import UnitConverter


class LocalizationUtils:
    """
    Utilities for locale-specific formatting and cultural adaptations.
    
    This class provides methods for formatting numbers, dates, currencies,
    and engineering units according to the current locale.
    """
    
    def __init__(self, unit_converter: Optional[UnitConverter] = None):
        """
        Initialize localization utilities.
        
        Args:
            unit_converter: Unit converter instance for engineering units
        """
        self.unit_converter = unit_converter
        self.logger = logging.getLogger(__name__)
        
        # Locale-specific unit system mappings
        self.locale_unit_systems = {
            "en_US": "Imperial",
            "en_GB": "SI_Engineering", 
            "en_CA": "SI_Engineering",
            "en_AU": "SI_Engineering",
            "es_ES": "SI_Engineering",
            "es_MX": "SI_Engineering",
            "fr_FR": "SI_Engineering",
            "fr_CA": "SI_Engineering",
            "de_DE": "SI_Engineering",
            "it_IT": "SI_Engineering",
            "pt_BR": "SI_Engineering",
            "ja_JP": "SI_Engineering",
            "ko_KR": "SI_Engineering",
            "zh_CN": "SI_Engineering",
            "zh_TW": "SI_Engineering",
            "ar_SA": "SI_Engineering",
            "he_IL": "SI_Engineering",
        }
        
        # Engineering code mappings by locale
        self.locale_engineering_codes = {
            "en_US": ["ACI 318", "AISC 360", "ASCE 7"],
            "en_CA": ["CSA A23.3", "CSA S16", "NBCC"],
            "en_GB": ["Eurocode 2", "Eurocode 3", "BS 8110"],
            "en_AU": ["AS 3600", "AS 4100", "AS 1170"],
            "es_ES": ["Eurocode 2", "Eurocode 3", "EHE-08"],
            "fr_FR": ["Eurocode 2", "Eurocode 3", "BAEL 91"],
            "de_DE": ["Eurocode 2", "Eurocode 3", "DIN 1045"],
            "it_IT": ["Eurocode 2", "Eurocode 3", "NTC 2018"],
            "pt_BR": ["NBR 6118", "NBR 8800", "NBR 6123"],
            "ja_JP": ["AIJ", "JSCE", "BCJ"],
            "zh_CN": ["GB 50010", "GB 50017", "GB 50009"],
        }
    
    def get_current_locale(self) -> Locale:
        """Get the current Babel locale object."""
        manager = get_i18n_manager()
        return manager.get_babel_locale() if manager else Locale.parse("en_US")
    
    def get_locale_unit_system(self, locale_code: Optional[str] = None) -> str:
        """
        Get the preferred unit system for a locale.
        
        Args:
            locale_code: Locale code (uses current if None)
            
        Returns:
            Unit system name
        """
        if locale_code is None:
            manager = get_i18n_manager()
            locale_code = manager.get_locale() if manager else "en_US"
        
        return self.locale_unit_systems.get(locale_code, "SI_Engineering")
    
    def get_locale_engineering_codes(self, locale_code: Optional[str] = None) -> List[str]:
        """
        Get preferred engineering codes for a locale.
        
        Args:
            locale_code: Locale code (uses current if None)
            
        Returns:
            List of engineering code names
        """
        if locale_code is None:
            manager = get_i18n_manager()
            locale_code = manager.get_locale() if manager else "en_US"
        
        return self.locale_engineering_codes.get(locale_code, ["ACI 318"])
    
    def format_engineering_number(self, value: Union[int, float, Decimal], 
                                 precision: int = 3, 
                                 use_scientific: bool = False) -> str:
        """
        Format a number for engineering display.
        
        Args:
            value: Number to format
            precision: Number of decimal places
            use_scientific: Whether to use scientific notation for large numbers
            
        Returns:
            Formatted number string
        """
        try:
            locale = self.get_current_locale()
            
            # Use scientific notation for very large or very small numbers
            if use_scientific or abs(value) >= 1e6 or (abs(value) < 1e-3 and value != 0):
                return format_scientific(value, locale=locale)
            else:
                # Format with specified precision
                format_str = f"#,##0.{'0' * precision}"
                return format_decimal(value, format=format_str, locale=locale)
                
        except Exception as e:
            self.logger.warning(f"Number formatting error: {e}")
            return f"{value:.{precision}f}"
    
    def format_engineering_value_with_unit(self, value: Union[int, float, Decimal], 
                                          unit: str, precision: int = 3) -> str:
        """
        Format an engineering value with its unit.
        
        Args:
            value: Numerical value
            unit: Unit string
            precision: Number of decimal places
            
        Returns:
            Formatted value with unit
        """
        formatted_value = self.format_engineering_number(value, precision)
        
        # Try to use Babel's unit formatting if available
        try:
            locale = self.get_current_locale()
            # Note: Babel's format_unit may not support all engineering units
            return format_unit(value, unit, locale=locale)
        except:
            # Fallback to simple concatenation
            return f"{formatted_value} {unit}"
    
    def format_datetime_engineering(self, dt: datetime, 
                                   include_seconds: bool = False) -> str:
        """
        Format datetime for engineering reports.
        
        Args:
            dt: Datetime to format
            include_seconds: Whether to include seconds
            
        Returns:
            Formatted datetime string
        """
        try:
            locale = self.get_current_locale()
            
            if include_seconds:
                format_str = "medium"
            else:
                format_str = "short"
            
            return format_datetime(dt, format_str, locale=locale)
            
        except Exception as e:
            self.logger.warning(f"Datetime formatting error: {e}")
            return dt.strftime("%Y-%m-%d %H:%M")
    
    def format_date_engineering(self, d: date) -> str:
        """
        Format date for engineering reports.
        
        Args:
            d: Date to format
            
        Returns:
            Formatted date string
        """
        try:
            locale = self.get_current_locale()
            return format_date(d, format="medium", locale=locale)
        except Exception as e:
            self.logger.warning(f"Date formatting error: {e}")
            return d.strftime("%Y-%m-%d")
    
    def get_decimal_separator(self) -> str:
        """Get the decimal separator for the current locale."""
        try:
            locale = self.get_current_locale()
            return locale.number_symbols.get('decimal', '.')
        except:
            return '.'
    
    def get_thousands_separator(self) -> str:
        """Get the thousands separator for the current locale."""
        try:
            locale = self.get_current_locale()
            return locale.number_symbols.get('group', ',')
        except:
            return ','
    
    def parse_localized_number(self, number_str: str) -> float:
        """
        Parse a localized number string.
        
        Args:
            number_str: Localized number string
            
        Returns:
            Parsed number
        """
        try:
            # Get locale-specific separators
            decimal_sep = self.get_decimal_separator()
            thousands_sep = self.get_thousands_separator()
            
            # Normalize the string
            normalized = number_str.replace(thousands_sep, '').replace(decimal_sep, '.')
            
            return float(normalized)
            
        except Exception as e:
            self.logger.error(f"Failed to parse localized number '{number_str}': {e}")
            raise ValueError(f"Invalid number format: {number_str}")
    
    def get_currency_symbol(self, currency_code: str = "USD") -> str:
        """
        Get currency symbol for the current locale.
        
        Args:
            currency_code: ISO currency code
            
        Returns:
            Currency symbol
        """
        try:
            locale = self.get_current_locale()
            return locale.currencies.get(currency_code, currency_code)
        except:
            return currency_code
    
    def format_percentage(self, value: Union[int, float, Decimal], 
                         precision: int = 1) -> str:
        """
        Format a percentage value.
        
        Args:
            value: Value to format (0.15 for 15%)
            precision: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        try:
            locale = self.get_current_locale()
            format_str = f"#,##0.{'0' * precision}%"
            return format_percent(value, format=format_str, locale=locale)
        except Exception as e:
            self.logger.warning(f"Percentage formatting error: {e}")
            return f"{value * 100:.{precision}f}%"
    
    def get_text_direction(self) -> str:
        """
        Get text direction for the current locale.
        
        Returns:
            'rtl' for right-to-left, 'ltr' for left-to-right
        """
        manager = get_i18n_manager()
        if manager and manager.is_rtl_locale():
            return 'rtl'
        return 'ltr'
    
    def adapt_ui_for_locale(self) -> Dict[str, Any]:
        """
        Get UI adaptation settings for the current locale.
        
        Returns:
            Dictionary with UI adaptation settings
        """
        text_direction = self.get_text_direction()
        locale = self.get_current_locale()
        
        return {
            'text_direction': text_direction,
            'is_rtl': text_direction == 'rtl',
            'decimal_separator': self.get_decimal_separator(),
            'thousands_separator': self.get_thousands_separator(),
            'date_format': 'medium',
            'number_format': 'decimal',
            'unit_system': self.get_locale_unit_system(),
            'engineering_codes': self.get_locale_engineering_codes(),
            'locale_code': locale.language if locale else 'en',
            'locale_display_name': locale.display_name if locale else 'English'
        }
    
    def convert_to_locale_units(self, value: Union[int, float, Decimal], 
                               from_unit: str, quantity_type: str) -> tuple[float, str]:
        """
        Convert a value to the preferred units for the current locale.
        
        Args:
            value: Value to convert
            from_unit: Source unit
            quantity_type: Type of quantity (e.g., 'length', 'force')
            
        Returns:
            Tuple of (converted_value, target_unit)
        """
        if not self.unit_converter:
            return float(value), from_unit
        
        try:
            target_system = self.get_locale_unit_system()
            target_unit = self.unit_converter.get_unit_for_quantity(quantity_type, target_system)
            converted_value = self.unit_converter.convert(value, from_unit, target_unit)
            
            return converted_value, target_unit
            
        except Exception as e:
            self.logger.warning(f"Unit conversion error: {e}")
            return float(value), from_unit
    
    def get_locale_specific_help_text(self, key: str) -> str:
        """
        Get locale-specific help text or documentation.
        
        Args:
            key: Help text key
            
        Returns:
            Localized help text
        """
        # This would typically load from locale-specific help files
        # For now, return a placeholder
        manager = get_i18n_manager()
        if manager:
            return manager.translate(f"help.{key}", "eng_struct_tools")
        return f"Help text for {key}"


# Global localization utilities instance
_l10n_utils: Optional[LocalizationUtils] = None


def get_l10n_utils() -> Optional[LocalizationUtils]:
    """Get the global localization utilities instance."""
    return _l10n_utils


def set_l10n_utils(utils: LocalizationUtils) -> None:
    """Set the global localization utilities instance."""
    global _l10n_utils
    _l10n_utils = utils


def format_engineering_number(value: Union[int, float, Decimal], precision: int = 3) -> str:
    """Convenience function for formatting engineering numbers."""
    utils = get_l10n_utils()
    return utils.format_engineering_number(value, precision) if utils else f"{value:.{precision}f}"


def format_engineering_value(value: Union[int, float, Decimal], unit: str, precision: int = 3) -> str:
    """Convenience function for formatting engineering values with units."""
    utils = get_l10n_utils()
    return utils.format_engineering_value_with_unit(value, unit, precision) if utils else f"{value:.{precision}f} {unit}"
