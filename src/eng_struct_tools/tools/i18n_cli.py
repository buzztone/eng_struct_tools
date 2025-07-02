#!/usr/bin/env python3
"""
Command-line interface for i18n/l10n management.

This script provides command-line tools for managing translations in the
Engineering Structural Tools application.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.tools.translation_manager import TranslationManager, StringExtractor


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def extract_strings(args) -> None:
    """Extract translatable strings from source code."""
    project_root = Path(args.project_root)
    manager = TranslationManager(project_root)
    
    print("Extracting translatable strings...")
    pot_file = manager.create_pot_file()
    print(f"Created POT file: {pot_file}")


def update_translations(args) -> None:
    """Update existing translation files."""
    project_root = Path(args.project_root)
    manager = TranslationManager(project_root)
    
    print("Updating translation files...")
    updated_files = manager.update_po_files()
    
    if updated_files:
        print(f"Updated {len(updated_files)} translation files:")
        for file_path in updated_files:
            print(f"  - {file_path}")
    else:
        print("No translation files found to update.")


def compile_translations(args) -> None:
    """Compile translation files to binary format."""
    project_root = Path(args.project_root)
    manager = TranslationManager(project_root)
    
    print("Compiling translation files...")
    compiled_files = manager.compile_mo_files()
    
    if compiled_files:
        print(f"Compiled {len(compiled_files)} translation files:")
        for file_path in compiled_files:
            print(f"  - {file_path}")
    else:
        print("No translation files found to compile.")


def validate_translations(args) -> None:
    """Validate translation completeness."""
    project_root = Path(args.project_root)
    manager = TranslationManager(project_root)
    
    print("Validating translations...")
    results = manager.validate_translations()
    
    if not results:
        print("No translation files found.")
        return
    
    print("\nTranslation Status:")
    print("-" * 60)
    print(f"{'Locale':<10} {'Total':<8} {'Translated':<12} {'Completion':<12}")
    print("-" * 60)
    
    for locale, data in results.items():
        if 'error' in data:
            print(f"{locale:<10} ERROR: {data['error']}")
        else:
            completion = f"{data['completion_rate']:.1f}%"
            print(f"{locale:<10} {data['total']:<8} {data['translated']:<12} {completion:<12}")
            
            if data['untranslated'] > 0:
                print(f"           {data['untranslated']} untranslated entries")
            if data['fuzzy'] > 0:
                print(f"           {data['fuzzy']} fuzzy entries")


def create_locale(args) -> None:
    """Create a new locale directory and PO file."""
    project_root = Path(args.project_root)
    locale_code = args.locale
    
    # Create locale directory structure
    locale_dir = project_root / "locales" / locale_code / "LC_MESSAGES"
    locale_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PO file from POT template
    pot_file = project_root / "locales" / "eng_struct_tools.pot"
    po_file = locale_dir / "eng_struct_tools.po"
    
    if not pot_file.exists():
        print(f"POT template file not found: {pot_file}")
        print("Run 'extract' command first to create the template.")
        return
    
    if po_file.exists() and not args.force:
        print(f"PO file already exists: {po_file}")
        print("Use --force to overwrite.")
        return
    
    try:
        import polib
        
        # Load POT template
        pot = polib.pofile(str(pot_file))
        
        # Update metadata for the new locale
        pot.metadata['Language'] = locale_code
        pot.metadata['Language-Team'] = f"{locale_code} <team@example.com>"
        
        # Save as PO file
        pot.save(str(po_file))
        
        print(f"Created new locale: {locale_code}")
        print(f"PO file: {po_file}")
        
    except Exception as e:
        print(f"Failed to create locale: {e}")


def list_strings(args) -> None:
    """List all translatable strings found in source code."""
    project_root = Path(args.project_root)
    src_dir = project_root / "src"
    
    extractor = StringExtractor()
    strings = extractor.extract_from_directory(src_dir)
    
    if not strings:
        print("No translatable strings found.")
        return
    
    print(f"Found {len(strings)} translatable strings:")
    print("-" * 60)
    
    for i, string_info in enumerate(strings, 1):
        print(f"{i:3d}. {string_info['msgid']}")
        print(f"     File: {string_info['file']}:{string_info['line']}")
        print(f"     Type: {string_info['type']}")
        
        if string_info['type'] == 'plural':
            print(f"     Plural: {string_info['msgid_plural']}")
        elif string_info['type'] == 'context':
            print(f"     Context: {string_info['msgctxt']}")
        
        print()


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="i18n/l10n management tool for Engineering Structural Tools"
    )
    
    parser.add_argument(
        "--project-root",
        type=str,
        default=str(project_root),
        help="Project root directory (default: auto-detected)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract translatable strings from source code"
    )
    extract_parser.set_defaults(func=extract_strings)
    
    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update existing translation files"
    )
    update_parser.set_defaults(func=update_translations)
    
    # Compile command
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile translation files to binary format"
    )
    compile_parser.set_defaults(func=compile_translations)
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate translation completeness"
    )
    validate_parser.set_defaults(func=validate_translations)
    
    # Create locale command
    create_parser = subparsers.add_parser(
        "create-locale",
        help="Create a new locale"
    )
    create_parser.add_argument(
        "locale",
        help="Locale code (e.g., 'es_ES', 'fr_FR')"
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files"
    )
    create_parser.set_defaults(func=create_locale)
    
    # List strings command
    list_parser = subparsers.add_parser(
        "list-strings",
        help="List all translatable strings"
    )
    list_parser.set_defaults(func=list_strings)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Execute command
    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
