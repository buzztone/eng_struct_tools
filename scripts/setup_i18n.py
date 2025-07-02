#!/usr/bin/env python3
"""
Setup script for i18n/l10n system.

This script initializes the translation system and creates the necessary
directory structure and initial translation files.
"""

import sys
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.tools.translation_manager import TranslationManager


def main():
    """Set up the i18n/l10n system."""
    print("Setting up i18n/l10n system for Engineering Structural Tools...")
    
    # Initialize translation manager
    manager = TranslationManager(project_root)
    
    # Create locales directory structure
    locales_dir = project_root / "locales"
    locales_dir.mkdir(exist_ok=True)
    
    print(f"Created locales directory: {locales_dir}")
    
    # Extract strings and create POT file
    print("\n1. Extracting translatable strings...")
    pot_file = manager.create_pot_file()
    print(f"   Created POT template: {pot_file}")
    
    # Create initial locale directories
    initial_locales = ["en_US", "es_ES", "fr_FR", "de_DE"]
    
    print("\n2. Creating initial locale directories...")
    for locale in initial_locales:
        locale_dir = locales_dir / locale / "LC_MESSAGES"
        locale_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Created: {locale_dir}")
    
    # Update existing PO files or create new ones
    print("\n3. Updating/creating PO files...")
    updated_files = manager.update_po_files()
    
    if updated_files:
        print(f"   Updated {len(updated_files)} PO files")
    else:
        print("   No existing PO files found")
    
    # Compile MO files
    print("\n4. Compiling MO files...")
    compiled_files = manager.compile_mo_files()
    print(f"   Compiled {len(compiled_files)} MO files")
    
    # Validate translations
    print("\n5. Validating translations...")
    results = manager.validate_translations()
    
    if results:
        print("   Translation status:")
        for locale, data in results.items():
            if 'error' not in data:
                completion = data['completion_rate']
                print(f"     {locale}: {completion:.1f}% complete")
    
    print("\n✅ i18n/l10n setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the PO files in the locales directories to add translations")
    print("2. Run 'python scripts/update_translations.py' to update translations")
    print("3. Use the i18n CLI tool for ongoing translation management:")
    print("   python src/eng_struct_tools/tools/i18n_cli.py --help")


if __name__ == "__main__":
    main()
