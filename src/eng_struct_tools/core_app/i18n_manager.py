"""
Internationalization (i18n) and Localization (l10n) Manager.

This module provides comprehensive internationalization and localization support
for the Engineering Structural Tools application, including translation management,
locale detection, and formatting utilities.
"""

import gettext
import logging
import os
import locale
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from threading import Lock
import weakref

from babel import Locale, UnknownLocaleError
from babel.dates import format_datetime, format_date, format_time
from babel.numbers import format_decimal, format_currency, format_percent
from babel.support import Translations
import polib

from .config import ConfigManager


class TranslationDomain:
    """
    Represents a translation domain for a specific component or plugin.
    
    Each domain manages its own set of translations and can be loaded/unloaded
    independently.
    """
    
    def __init__(self, domain_name: str, locale_dir: Path, fallback_locale: str = "en_US"):
        """
        Initialize a translation domain.
        
        Args:
            domain_name: Unique name for this translation domain
            locale_dir: Directory containing locale files
            fallback_locale: Fallback locale if requested locale not available
        """
        self.domain_name = domain_name
        self.locale_dir = locale_dir
        self.fallback_locale = fallback_locale
        self.translations: Dict[str, gettext.GNUTranslations] = {}
        self.current_locale = fallback_locale
        self.logger = logging.getLogger(__name__)
    
    def load_translation(self, locale_code: str) -> bool:
        """
        Load translation for a specific locale.
        
        Args:
            locale_code: Locale code (e.g., 'en_US', 'es_ES')
            
        Returns:
            True if translation loaded successfully, False otherwise
        """
        try:
            mo_file = self.locale_dir / locale_code / "LC_MESSAGES" / f"{self.domain_name}.mo"
            
            if mo_file.exists():
                with open(mo_file, 'rb') as f:
                    translation = gettext.GNUTranslations(f)
                    self.translations[locale_code] = translation
                    self.logger.debug(f"Loaded translation for {self.domain_name}:{locale_code}")
                    return True
            else:
                self.logger.warning(f"Translation file not found: {mo_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to load translation {self.domain_name}:{locale_code}: {e}")
            return False
    
    def get_translation(self, locale_code: str) -> Optional[gettext.GNUTranslations]:
        """Get translation for a specific locale."""
        if locale_code not in self.translations:
            self.load_translation(locale_code)
        
        return self.translations.get(locale_code)
    
    def translate(self, message: str, locale_code: str, context: Optional[str] = None) -> str:
        """
        Translate a message.
        
        Args:
            message: Message to translate
            locale_code: Target locale
            context: Optional context for disambiguation
            
        Returns:
            Translated message or original if translation not found
        """
        translation = self.get_translation(locale_code)
        
        if translation:
            try:
                if context:
                    # Use pgettext for contextual translations
                    return translation.pgettext(context, message)
                else:
                    return translation.gettext(message)
            except Exception as e:
                self.logger.warning(f"Translation error for '{message}': {e}")
        
        # Fallback to original message
        return message
    
    def ngettext(self, singular: str, plural: str, n: int, locale_code: str) -> str:
        """
        Translate with pluralization support.
        
        Args:
            singular: Singular form
            plural: Plural form
            n: Number for pluralization
            locale_code: Target locale
            
        Returns:
            Appropriate plural form
        """
        translation = self.get_translation(locale_code)
        
        if translation:
            try:
                return translation.ngettext(singular, plural, n)
            except Exception as e:
                self.logger.warning(f"Pluralization error: {e}")
        
        # Fallback to simple English pluralization
        return singular if n == 1 else plural


class I18nManager:
    """
    Central manager for internationalization and localization.
    
    This class coordinates translation domains, manages locale settings,
    and provides utilities for formatting locale-specific data.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the i18n manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Translation domains registry
        self.domains: Dict[str, TranslationDomain] = {}
        
        # Current locale settings
        self.current_locale = self._detect_locale()
        self.current_babel_locale: Optional[Locale] = None
        
        # Thread safety
        self._lock = Lock()
        
        # Observers for locale changes
        self._locale_observers: List[Callable[[str], None]] = []
        
        # Initialize core domain
        self._initialize_core_domain()
        
        # Set up Babel locale
        self._update_babel_locale()
        
        self.logger.info(f"I18n manager initialized with locale: {self.current_locale}")
    
    def _detect_locale(self) -> str:
        """Detect the appropriate locale for the user."""
        # First, check user configuration
        user_locale = self.config_manager.get_setting("i18n/locale")
        if user_locale:
            return user_locale
        
        # Try to detect system locale
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                return system_locale
        except Exception as e:
            self.logger.warning(f"Failed to detect system locale: {e}")
        
        # Fallback to English
        return "en_US"
    
    def _initialize_core_domain(self) -> None:
        """Initialize the core application translation domain."""
        # Get the application root directory
        app_root = Path(__file__).parent.parent.parent.parent
        core_locale_dir = app_root / "locales"
        
        # Create core domain
        core_domain = TranslationDomain("eng_struct_tools", core_locale_dir)
        self.register_domain(core_domain)
    
    def _update_babel_locale(self) -> None:
        """Update the Babel locale object."""
        try:
            self.current_babel_locale = Locale.parse(self.current_locale)
        except UnknownLocaleError:
            self.logger.warning(f"Unknown locale: {self.current_locale}, using en_US")
            self.current_babel_locale = Locale.parse("en_US")
    
    def register_domain(self, domain: TranslationDomain) -> None:
        """
        Register a translation domain.
        
        Args:
            domain: Translation domain to register
        """
        with self._lock:
            self.domains[domain.domain_name] = domain
            self.logger.info(f"Registered translation domain: {domain.domain_name}")
    
    def unregister_domain(self, domain_name: str) -> None:
        """
        Unregister a translation domain.
        
        Args:
            domain_name: Name of domain to unregister
        """
        with self._lock:
            if domain_name in self.domains:
                del self.domains[domain_name]
                self.logger.info(f"Unregistered translation domain: {domain_name}")
    
    def set_locale(self, locale_code: str) -> bool:
        """
        Set the current locale.
        
        Args:
            locale_code: Locale code to set
            
        Returns:
            True if locale set successfully, False otherwise
        """
        try:
            # Validate locale
            Locale.parse(locale_code)
            
            with self._lock:
                old_locale = self.current_locale
                self.current_locale = locale_code
                self._update_babel_locale()
                
                # Save to configuration
                self.config_manager.set_setting("i18n/locale", locale_code)
                
                # Notify observers
                for observer in self._locale_observers:
                    try:
                        observer(locale_code)
                    except Exception as e:
                        self.logger.error(f"Error notifying locale observer: {e}")
                
                self.logger.info(f"Locale changed from {old_locale} to {locale_code}")
                return True
                
        except UnknownLocaleError:
            self.logger.error(f"Invalid locale code: {locale_code}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to set locale: {e}")
            return False
    
    def get_locale(self) -> str:
        """Get the current locale code."""
        return self.current_locale
    
    def get_babel_locale(self) -> Locale:
        """Get the current Babel locale object."""
        return self.current_babel_locale or Locale.parse("en_US")
    
    def add_locale_observer(self, observer: Callable[[str], None]) -> None:
        """
        Add an observer for locale changes.
        
        Args:
            observer: Callback function that receives the new locale code
        """
        self._locale_observers.append(observer)
    
    def remove_locale_observer(self, observer: Callable[[str], None]) -> None:
        """Remove a locale observer."""
        if observer in self._locale_observers:
            self._locale_observers.remove(observer)
    
    def translate(self, message: str, domain: str = "eng_struct_tools", 
                 context: Optional[str] = None) -> str:
        """
        Translate a message.
        
        Args:
            message: Message to translate
            domain: Translation domain name
            context: Optional context for disambiguation
            
        Returns:
            Translated message
        """
        if domain in self.domains:
            return self.domains[domain].translate(message, self.current_locale, context)
        else:
            self.logger.warning(f"Unknown translation domain: {domain}")
            return message
    
    def ngettext(self, singular: str, plural: str, n: int, 
                domain: str = "eng_struct_tools") -> str:
        """
        Translate with pluralization support.
        
        Args:
            singular: Singular form
            plural: Plural form
            n: Number for pluralization
            domain: Translation domain name
            
        Returns:
            Appropriate plural form
        """
        if domain in self.domains:
            return self.domains[domain].ngettext(singular, plural, n, self.current_locale)
        else:
            return singular if n == 1 else plural
    
    def get_available_locales(self) -> List[str]:
        """
        Get list of available locales across all domains.
        
        Returns:
            List of available locale codes
        """
        locales = set()
        
        for domain in self.domains.values():
            if domain.locale_dir.exists():
                for locale_dir in domain.locale_dir.iterdir():
                    if locale_dir.is_dir() and (locale_dir / "LC_MESSAGES").exists():
                        locales.add(locale_dir.name)
        
        return sorted(list(locales))
    
    def format_number(self, number: Union[int, float], format_type: str = "decimal") -> str:
        """
        Format a number according to current locale.
        
        Args:
            number: Number to format
            format_type: Type of formatting ('decimal', 'currency', 'percent')
            
        Returns:
            Formatted number string
        """
        try:
            if format_type == "decimal":
                return format_decimal(number, locale=self.current_babel_locale)
            elif format_type == "currency":
                return format_currency(number, "USD", locale=self.current_babel_locale)
            elif format_type == "percent":
                return format_percent(number, locale=self.current_babel_locale)
            else:
                return str(number)
        except Exception as e:
            self.logger.warning(f"Number formatting error: {e}")
            return str(number)
    
    def format_datetime(self, dt, format_type: str = "medium") -> str:
        """
        Format a datetime according to current locale.
        
        Args:
            dt: Datetime object to format
            format_type: Format type ('short', 'medium', 'long', 'full')
            
        Returns:
            Formatted datetime string
        """
        try:
            return format_datetime(dt, format_type, locale=self.current_babel_locale)
        except Exception as e:
            self.logger.warning(f"Datetime formatting error: {e}")
            return str(dt)
    
    def is_rtl_locale(self) -> bool:
        """Check if current locale uses right-to-left text direction."""
        rtl_locales = ['ar', 'he', 'fa', 'ur']  # Arabic, Hebrew, Persian, Urdu
        return any(self.current_locale.startswith(lang) for lang in rtl_locales)


# Global i18n manager instance (will be initialized by the main application)
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager() -> Optional[I18nManager]:
    """Get the global i18n manager instance."""
    return _i18n_manager


def set_i18n_manager(manager: I18nManager) -> None:
    """Set the global i18n manager instance."""
    global _i18n_manager
    _i18n_manager = manager


# Convenience functions for common translation operations
def _(message: str, domain: str = "eng_struct_tools") -> str:
    """Translate a message (gettext-style shorthand)."""
    manager = get_i18n_manager()
    return manager.translate(message, domain) if manager else message


def ngettext(singular: str, plural: str, n: int, domain: str = "eng_struct_tools") -> str:
    """Translate with pluralization support."""
    manager = get_i18n_manager()
    return manager.ngettext(singular, plural, n, domain) if manager else (singular if n == 1 else plural)


def pgettext(context: str, message: str, domain: str = "eng_struct_tools") -> str:
    """Translate with context support."""
    manager = get_i18n_manager()
    return manager.translate(message, domain, context) if manager else message
