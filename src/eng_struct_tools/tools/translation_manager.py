"""
Translation management tools for the Engineering Structural Tools application.

This module provides utilities for extracting translatable strings, managing
translation files, and validating translation completeness.
"""

import os
import re
import ast
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import subprocess
import sys

import polib
from babel.messages import Catalog
from babel.messages.extract import extract_from_dir
from babel.messages.pofile import write_po, read_po


class StringExtractor:
    """
    Utility for extracting translatable strings from Python source code.
    
    This class scans Python files for translation function calls and extracts
    the strings for translation.
    """
    
    def __init__(self):
        """Initialize the string extractor."""
        self.logger = logging.getLogger(__name__)
        
        # Translation function patterns
        self.translation_functions = {
            '_': 1,           # _(message)
            'ngettext': 3,    # ngettext(singular, plural, n)
            'pgettext': 2,    # pgettext(context, message)
            'translate': 1,   # translate(message)
        }
        
        # Regex patterns for finding translation calls
        self.patterns = {
            '_': re.compile(r'_\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            'ngettext': re.compile(r'ngettext\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*,'),
            'pgettext': re.compile(r'pgettext\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'),
        }
    
    def extract_from_file(self, file_path: Path) -> List[Dict]:
        """
        Extract translatable strings from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of extracted string dictionaries
        """
        strings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use AST for more accurate extraction
            try:
                tree = ast.parse(content, filename=str(file_path))
                strings.extend(self._extract_from_ast(tree, file_path))
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                # Fallback to regex extraction
                strings.extend(self._extract_with_regex(content, file_path))
            
        except Exception as e:
            self.logger.error(f"Failed to extract strings from {file_path}: {e}")
        
        return strings
    
    def _extract_from_ast(self, tree: ast.AST, file_path: Path) -> List[Dict]:
        """Extract strings using AST parsing."""
        strings = []
        
        class TranslationVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    if func_name == '_' and len(node.args) >= 1:
                        if isinstance(node.args[0], ast.Constant):
                            strings.append({
                                'msgid': node.args[0].value,
                                'msgstr': '',
                                'file': str(file_path),
                                'line': node.lineno,
                                'type': 'simple'
                            })
                    
                    elif func_name == 'ngettext' and len(node.args) >= 2:
                        if (isinstance(node.args[0], ast.Constant) and 
                            isinstance(node.args[1], ast.Constant)):
                            strings.append({
                                'msgid': node.args[0].value,
                                'msgid_plural': node.args[1].value,
                                'msgstr': ['', ''],
                                'file': str(file_path),
                                'line': node.lineno,
                                'type': 'plural'
                            })
                    
                    elif func_name == 'pgettext' and len(node.args) >= 2:
                        if (isinstance(node.args[0], ast.Constant) and 
                            isinstance(node.args[1], ast.Constant)):
                            strings.append({
                                'msgctxt': node.args[0].value,
                                'msgid': node.args[1].value,
                                'msgstr': '',
                                'file': str(file_path),
                                'line': node.lineno,
                                'type': 'context'
                            })
                
                self.generic_visit(node)
        
        visitor = TranslationVisitor()
        visitor.visit(tree)
        
        return strings
    
    def _extract_with_regex(self, content: str, file_path: Path) -> List[Dict]:
        """Fallback regex-based extraction."""
        strings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Simple _ function calls
            for match in self.patterns['_'].finditer(line):
                strings.append({
                    'msgid': match.group(1),
                    'msgstr': '',
                    'file': str(file_path),
                    'line': line_num,
                    'type': 'simple'
                })
            
            # ngettext calls
            for match in self.patterns['ngettext'].finditer(line):
                strings.append({
                    'msgid': match.group(1),
                    'msgid_plural': match.group(2),
                    'msgstr': ['', ''],
                    'file': str(file_path),
                    'line': line_num,
                    'type': 'plural'
                })
            
            # pgettext calls
            for match in self.patterns['pgettext'].finditer(line):
                strings.append({
                    'msgctxt': match.group(1),
                    'msgid': match.group(2),
                    'msgstr': '',
                    'file': str(file_path),
                    'line': line_num,
                    'type': 'context'
                })
        
        return strings
    
    def extract_from_directory(self, directory: Path, 
                             exclude_patterns: Optional[List[str]] = None) -> List[Dict]:
        """
        Extract strings from all Python files in a directory.
        
        Args:
            directory: Directory to scan
            exclude_patterns: List of patterns to exclude
            
        Returns:
            List of extracted string dictionaries
        """
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', 'build', 'dist', 'tests']
        
        all_strings = []
        
        for py_file in directory.rglob('*.py'):
            # Check if file should be excluded
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue
            
            strings = self.extract_from_file(py_file)
            all_strings.extend(strings)
        
        return all_strings


class TranslationManager:
    """
    Manager for translation files and operations.
    
    This class provides high-level operations for managing translation
    catalogs, updating translations, and validating completeness.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the translation manager.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.locales_dir = project_root / "locales"
        self.logger = logging.getLogger(__name__)
        self.extractor = StringExtractor()
    
    def create_pot_file(self, output_file: Optional[Path] = None) -> Path:
        """
        Create a POT (Portable Object Template) file from source code.
        
        Args:
            output_file: Output file path (default: locales/project.pot)
            
        Returns:
            Path to the created POT file
        """
        if output_file is None:
            output_file = self.locales_dir / "eng_struct_tools.pot"
        
        # Extract strings from source code
        src_dir = self.project_root / "src"
        strings = self.extractor.extract_from_directory(src_dir)
        
        # Create catalog
        catalog = Catalog(
            project="Engineering Structural Tools",
            version="0.1.0",
            copyright_holder="Neil Murray",
            msgid_bugs_address="neilmrr75@gmail.com",
            creation_date=None,
            revision_date=None,
            fuzzy=False
        )
        
        # Add strings to catalog
        for string_info in strings:
            if string_info['type'] == 'simple':
                catalog.add(
                    string_info['msgid'],
                    locations=[(string_info['file'], string_info['line'])]
                )
            elif string_info['type'] == 'plural':
                catalog.add(
                    string_info['msgid'],
                    string_info['msgid_plural'],
                    locations=[(string_info['file'], string_info['line'])]
                )
            elif string_info['type'] == 'context':
                catalog.add(
                    string_info['msgid'],
                    context=string_info['msgctxt'],
                    locations=[(string_info['file'], string_info['line'])]
                )
        
        # Write POT file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'wb') as f:
            write_po(f, catalog)
        
        self.logger.info(f"Created POT file: {output_file}")
        return output_file
    
    def update_po_files(self, pot_file: Optional[Path] = None) -> List[Path]:
        """
        Update existing PO files with new strings from POT file.
        
        Args:
            pot_file: POT file to use as template
            
        Returns:
            List of updated PO file paths
        """
        if pot_file is None:
            pot_file = self.locales_dir / "eng_struct_tools.pot"
        
        if not pot_file.exists():
            self.logger.error(f"POT file not found: {pot_file}")
            return []
        
        updated_files = []
        
        # Find all existing PO files
        for po_file in self.locales_dir.rglob("*.po"):
            try:
                # Read existing PO file
                with open(po_file, 'rb') as f:
                    catalog = read_po(f)
                
                # Read POT template
                with open(pot_file, 'rb') as f:
                    template = read_po(f)
                
                # Update catalog with new strings
                catalog.update(template)
                
                # Write updated PO file
                with open(po_file, 'wb') as f:
                    write_po(f, catalog)
                
                updated_files.append(po_file)
                self.logger.info(f"Updated PO file: {po_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to update {po_file}: {e}")
        
        return updated_files
    
    def compile_mo_files(self) -> List[Path]:
        """
        Compile PO files to MO files.
        
        Returns:
            List of compiled MO file paths
        """
        compiled_files = []
        
        for po_file in self.locales_dir.rglob("*.po"):
            try:
                mo_file = po_file.with_suffix('.mo')
                
                # Read PO file
                po = polib.pofile(str(po_file))
                
                # Save as MO file
                po.save_as_mofile(str(mo_file))
                
                compiled_files.append(mo_file)
                self.logger.info(f"Compiled MO file: {mo_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to compile {po_file}: {e}")
        
        return compiled_files
    
    def validate_translations(self) -> Dict[str, Dict]:
        """
        Validate translation completeness and consistency.
        
        Returns:
            Dictionary with validation results for each locale
        """
        results = {}
        
        for po_file in self.locales_dir.rglob("*.po"):
            locale = po_file.parent.parent.name
            
            try:
                po = polib.pofile(str(po_file))
                
                total_entries = len(po)
                translated_entries = len(po.translated_entries())
                untranslated_entries = len(po.untranslated_entries())
                fuzzy_entries = len(po.fuzzy_entries())
                
                completion_rate = (translated_entries / total_entries * 100) if total_entries > 0 else 0
                
                results[locale] = {
                    'file': str(po_file),
                    'total': total_entries,
                    'translated': translated_entries,
                    'untranslated': untranslated_entries,
                    'fuzzy': fuzzy_entries,
                    'completion_rate': completion_rate
                }
                
            except Exception as e:
                self.logger.error(f"Failed to validate {po_file}: {e}")
                results[locale] = {'error': str(e)}
        
        return results
