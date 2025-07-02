#!/usr/bin/env python3
"""
Update script for translations.

This script updates all translation files with new strings from the source code
and compiles them to binary format.
"""

import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eng_struct_tools.tools.translation_manager import TranslationManager


def main():
    """Update all translations."""
    print("Updating translations for Engineering Structural Tools...")
    
    # Initialize translation manager
    manager = TranslationManager(project_root)
    
    # Extract new strings and update POT file
    print("\n1. Extracting new translatable strings...")
    pot_file = manager.create_pot_file()
    print(f"   Updated POT template: {pot_file}")
    
    # Update all PO files
    print("\n2. Updating PO files...")
    updated_files = manager.update_po_files()
    
    if updated_files:
        print(f"   Updated {len(updated_files)} PO files:")
        for file_path in updated_files:
            print(f"     - {file_path}")
    else:
        print("   No PO files found to update")
    
    # Compile MO files
    print("\n3. Compiling MO files...")
    compiled_files = manager.compile_mo_files()
    
    if compiled_files:
        print(f"   Compiled {len(compiled_files)} MO files:")
        for file_path in compiled_files:
            print(f"     - {file_path}")
    else:
        print("   No PO files found to compile")
    
    # Validate translations
    print("\n4. Validating translations...")
    results = manager.validate_translations()
    
    if results:
        print("\n   Translation Status Report:")
        print("   " + "-" * 50)
        print(f"   {'Locale':<10} {'Completion':<12} {'Status'}")
        print("   " + "-" * 50)
        
        for locale, data in results.items():
            if 'error' in data:
                print(f"   {locale:<10} ERROR        {data['error']}")
            else:
                completion = f"{data['completion_rate']:.1f}%"
                status = "Complete" if data['completion_rate'] == 100 else "Incomplete"
                print(f"   {locale:<10} {completion:<12} {status}")
                
                if data['untranslated'] > 0:
                    print(f"   {'':10} {data['untranslated']} untranslated entries")
                if data['fuzzy'] > 0:
                    print(f"   {'':10} {data['fuzzy']} fuzzy entries")
    
    print("\n✅ Translation update completed!")
    print("\nTo translate strings:")
    print("1. Edit the .po files in the locales directories")
    print("2. Use a translation editor like Poedit for better workflow")
    print("3. Run this script again to compile the updated translations")


if __name__ == "__main__":
    main()
