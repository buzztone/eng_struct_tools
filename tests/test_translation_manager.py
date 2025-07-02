"""
Unit tests for the translation management tools.

This module contains tests for string extraction and translation
file management functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.tools.translation_manager import (
    StringExtractor, TranslationManager
)


class TestStringExtractor(unittest.TestCase):
    """Test cases for StringExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = StringExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_extract_simple_translation(self):
        """Test extracting simple translation calls."""
        # Create a test Python file
        test_file = self.temp_dir / "test.py"
        test_content = '''
def test_function():
    message = _("Hello, world!")
    return message
'''
        test_file.write_text(test_content, encoding='utf-8')
        
        # Extract strings
        strings = self.extractor.extract_from_file(test_file)
        
        # Verify extraction
        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0]['msgid'], "Hello, world!")
        self.assertEqual(strings[0]['type'], 'simple')
        self.assertEqual(strings[0]['line'], 3)
    
    def test_extract_ngettext_translation(self):
        """Test extracting ngettext calls."""
        test_file = self.temp_dir / "test.py"
        test_content = '''
def test_function(count):
    return ngettext("1 item", "{count} items", count)
'''
        test_file.write_text(test_content, encoding='utf-8')
        
        strings = self.extractor.extract_from_file(test_file)
        
        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0]['msgid'], "1 item")
        self.assertEqual(strings[0]['msgid_plural'], "{count} items")
        self.assertEqual(strings[0]['type'], 'plural')
    
    def test_extract_pgettext_translation(self):
        """Test extracting pgettext calls."""
        test_file = self.temp_dir / "test.py"
        test_content = '''
def test_function():
    return pgettext("menu", "File")
'''
        test_file.write_text(test_content, encoding='utf-8')
        
        strings = self.extractor.extract_from_file(test_file)
        
        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0]['msgctxt'], "menu")
        self.assertEqual(strings[0]['msgid'], "File")
        self.assertEqual(strings[0]['type'], 'context')
    
    def test_extract_from_directory(self):
        """Test extracting strings from a directory."""
        # Create multiple test files
        test_file1 = self.temp_dir / "file1.py"
        test_file1.write_text('message1 = _("Message 1")', encoding='utf-8')
        
        test_file2 = self.temp_dir / "file2.py"
        test_file2.write_text('message2 = _("Message 2")', encoding='utf-8')
        
        # Create a subdirectory with another file
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        test_file3 = subdir / "file3.py"
        test_file3.write_text('message3 = _("Message 3")', encoding='utf-8')
        
        # Extract strings
        strings = self.extractor.extract_from_directory(self.temp_dir)
        
        # Should find all three strings
        self.assertEqual(len(strings), 3)
        messages = [s['msgid'] for s in strings]
        self.assertIn("Message 1", messages)
        self.assertIn("Message 2", messages)
        self.assertIn("Message 3", messages)
    
    def test_extract_with_syntax_error(self):
        """Test extraction from file with syntax error."""
        test_file = self.temp_dir / "bad_syntax.py"
        test_content = '''
def test_function(
    # Missing closing parenthesis and colon
    message = _("Hello, world!")
'''
        test_file.write_text(test_content, encoding='utf-8')
        
        # Should not raise exception, should fallback to regex
        strings = self.extractor.extract_from_file(test_file)
        
        # Should still extract the string using regex fallback
        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0]['msgid'], "Hello, world!")
    
    def test_exclude_patterns(self):
        """Test excluding files based on patterns."""
        # Create files in excluded directories
        test_dir = self.temp_dir / "__pycache__"
        test_dir.mkdir()
        test_file = test_dir / "cached.py"
        test_file.write_text('message = _("Should be excluded")', encoding='utf-8')
        
        # Create normal file
        normal_file = self.temp_dir / "normal.py"
        normal_file.write_text('message = _("Should be included")', encoding='utf-8')
        
        strings = self.extractor.extract_from_directory(self.temp_dir)
        
        # Should only find the normal file
        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0]['msgid'], "Should be included")


class TestTranslationManager(unittest.TestCase):
    """Test cases for TranslationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TranslationManager(self.temp_dir)
        
        # Create a mock source directory with test files
        self.src_dir = self.temp_dir / "src"
        self.src_dir.mkdir()
        
        test_file = self.src_dir / "test.py"
        test_content = '''
def test_function():
    return _("Test message")
'''
        test_file.write_text(test_content, encoding='utf-8')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('src.eng_struct_tools.tools.translation_manager.write_po')
    @patch('src.eng_struct_tools.tools.translation_manager.Catalog')
    def test_create_pot_file(self, mock_catalog_class, mock_write_po):
        """Test creating a POT file."""
        mock_catalog = Mock()
        mock_catalog_class.return_value = mock_catalog
        
        pot_file = self.manager.create_pot_file()
        
        # Verify catalog was created and configured
        mock_catalog_class.assert_called_once()
        mock_catalog.add.assert_called()
        
        # Verify POT file path
        expected_path = self.temp_dir / "locales" / "eng_struct_tools.pot"
        self.assertEqual(pot_file, expected_path)
    
    def test_validate_translations_no_files(self):
        """Test validation when no translation files exist."""
        results = self.manager.validate_translations()
        self.assertEqual(len(results), 0)
    
    @patch('polib.pofile')
    def test_validate_translations_with_files(self, mock_pofile):
        """Test validation with existing translation files."""
        # Create a mock PO file
        mock_po = Mock()
        mock_po.__len__ = Mock(return_value=10)  # Total entries
        mock_po.translated_entries.return_value = [Mock()] * 7  # 7 translated
        mock_po.untranslated_entries.return_value = [Mock()] * 2  # 2 untranslated
        mock_po.fuzzy_entries.return_value = [Mock()]  # 1 fuzzy
        
        mock_pofile.return_value = mock_po
        
        # Create a test PO file
        locale_dir = self.temp_dir / "locales" / "es_ES" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_file = locale_dir / "test.po"
        po_file.write_text("# Test PO file", encoding='utf-8')
        
        results = self.manager.validate_translations()
        
        self.assertEqual(len(results), 1)
        self.assertIn("es_ES", results)
        
        result = results["es_ES"]
        self.assertEqual(result['total'], 10)
        self.assertEqual(result['translated'], 7)
        self.assertEqual(result['untranslated'], 2)
        self.assertEqual(result['fuzzy'], 1)
        self.assertEqual(result['completion_rate'], 70.0)
    
    @patch('polib.pofile')
    def test_compile_mo_files(self, mock_pofile):
        """Test compiling PO files to MO files."""
        # Create a mock PO file
        mock_po = Mock()
        mock_pofile.return_value = mock_po
        
        # Create a test PO file
        locale_dir = self.temp_dir / "locales" / "es_ES" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_file = locale_dir / "test.po"
        po_file.write_text("# Test PO file", encoding='utf-8')
        
        compiled_files = self.manager.compile_mo_files()
        
        # Verify MO file was created
        self.assertEqual(len(compiled_files), 1)
        expected_mo_file = locale_dir / "test.mo"
        self.assertEqual(compiled_files[0], expected_mo_file)
        
        # Verify save_as_mofile was called
        mock_po.save_as_mofile.assert_called_once()


class TestTranslationManagerIntegration(unittest.TestCase):
    """Integration tests for translation management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TranslationManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_simulation(self):
        """Test a complete translation workflow simulation."""
        # Create source files with translatable strings
        src_dir = self.temp_dir / "src"
        src_dir.mkdir()
        
        test_file = src_dir / "app.py"
        test_content = '''
class App:
    def __init__(self):
        self.title = _("Application Title")
        self.message = _("Welcome message")
    
    def show_items(self, count):
        return ngettext("1 item", "{count} items", count)
'''
        test_file.write_text(test_content, encoding='utf-8')
        
        # Extract strings (this would normally create a POT file)
        extractor = StringExtractor()
        strings = extractor.extract_from_directory(src_dir)
        
        # Verify extraction found the expected strings
        self.assertEqual(len(strings), 3)
        
        messages = [s['msgid'] for s in strings]
        self.assertIn("Application Title", messages)
        self.assertIn("Welcome message", messages)
        self.assertIn("1 item", messages)
        
        # Verify plural form was detected
        plural_strings = [s for s in strings if s['type'] == 'plural']
        self.assertEqual(len(plural_strings), 1)
        self.assertEqual(plural_strings[0]['msgid_plural'], "{count} items")


if __name__ == "__main__":
    unittest.main()
