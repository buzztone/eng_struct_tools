# Engineering Structural Tools

A modular plugin-based application for structural engineering analysis and design, built with PyQt6 and Python.

## Overview

Engineering Structural Tools is a software platform designed for structural engineers to perform various analysis and design tasks. The application follows a plugin-oriented architecture (POA) that allows for easy extension and customization while maintaining a unified user experience.

## Features

### Core Application
- **Plugin-based Architecture**: Modular design allows easy addition of new tools
- **Unified Interface**: Consistent user experience across all plugins
- **Configuration Management**: Centralized settings with persistence
- **Unit Management**: Unit conversion and system support
- **IFC Integration**: Built-in support for Industry Foundation Classes (IFC) data exchange
- **Logging System**: Logging for debugging and audit trails

### Current Plugins
- **Footing Design**: Concrete footing design and analysis tool
  - Bearing capacity checks
  - Reinforcement design
  - Multiple design code support (ACI 318, Eurocode 2, AS 3600, CSA A23.3)
  - Interactive parameter input and results display

### Planned Plugins
- Steel beam design
- Steel connection design
- Reinforced conrete slab design
- Wind load analysis

## Installation

### Prerequisites
- Python 3.12 or higher
- Poetry (for dependency management)

### Dependencies
- PyQt6: GUI framework
- ifcopenshell: IFC file handling
- pint: Unit conversion
- numpy: Numerical computations
- matplotlib: Plotting and visualization
- pydantic: Data validation

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/buzztone/eng_struct_tools.git
   cd eng_struct_tools
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Run the application:
   ```bash
   python -m src.eng_struct_tools.core_app.main
   ```

## Usage

### Starting the Application
Launch the application using the command above. The main window will appear with a menu system for accessing different tools.

### Using Plugins
1. Select a tool from the **Tools** menu
2. Enter the required parameters in the input panel
3. Click **Calculate** to run the analysis or design
4. Review results in the output panel
5. Export results if needed

### Configuration
- Access settings through the application menu
- Configure units, default values, and plugin preferences
- Settings are automatically saved and restored

## Development

### Project Structure
```
eng_struct_tools/
├── src/eng_struct_tools/
│   ├── core_app/           # Core application components
│   │   ├── main.py         # Main application entry point
│   │   ├── plugin_manager.py  # Plugin management
│   │   ├── config.py       # Configuration management
│   │   └── plugin_base.py  # Plugin base classes
│   ├── shared_libs/        # Shared utilities
│   │   ├── common_ui_widgets.py  # UI components
│   │   ├── unit_converter.py     # Unit conversion
│   │   └── ifc_utils.py    # IFC utilities
│   └── plugins/            # Plugin implementations
│       └── footing_design/ # Footing design plugin
├── tests/                  # Unit tests
├── docs/                   # Documentation
└── pyproject.toml         # Project configuration
```

### Creating a New Plugin
1. Create a new directory under `src/eng_struct_tools/plugins/`
2. Implement the plugin class inheriting from `PluginBase` or specialized base classes
3. Add entry point in `pyproject.toml`
4. Implement required methods:
   - `get_plugin_info()`
   - `initialize()`
   - `get_menu_items()`
   - `create_main_widget()`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Coding Standards
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add unit tests for new functionality
- Maintain backwards compatibility

## Contact

- **Author**: Neil Murray
- **Email**: neilmrr75@gmail.com
- **GitHub**: https://github.com/buzztone/eng_struct_tools

## Known Issues

- IFC library dependencies may require manual installation on some systems
- Unit tests require mock objects for PyQt6 components
- Plugin hot-reloading not yet implemented
- Export functionality in plugins is placeholder

## TODO Items for Future Development

### Core Application
- [ ] Implement project file management (new/open/save projects)
- [ ] Add plugin hot-reloading capability
- [ ] Enhance error handling with user-friendly error dialogs
- [ ] Implement application themes and customization
- [ ] Add comprehensive help system and user documentation

### Plugin System
- [ ] Create plugin template generator
- [ ] Implement plugin dependency management
- [ ] Add plugin configuration UI
- [ ] Create plugin marketplace/repository system
- [ ] Implement plugin versioning and updates

### Shared Libraries
- [ ] Complete IFC utilities implementation with full schema support
- [ ] Add advanced plotting and visualization tools
- [ ] Implement reporting system
- [ ] Add data import/export utilities (Excel, CSV, etc.)
- [ ] Create material property database
- [x] Internationalization (i18n) & Localization (l10n) Framework
- [ ] User Roles & Capabilities for Plugin Access/Usage

### Testing and Quality
- [ ] Increase test coverage to >90%
- [ ] Add integration tests for plugin system
- [ ] Implement automated UI testing
- [ ] Add performance benchmarking
- [ ] Create continuous integration pipeline

### Documentation
- [ ] Write user manual
- [ ] Create developer documentation
- [ ] Add API reference documentation
- [ ] Create video tutorials
- [ ] Write plugin development guide

## Internationalization (i18n) & Localization (l10n)

Engineering Structural Tools includes comprehensive support for multiple languages and locales.

### Supported Languages

- **English (en_US)** - Default language
- **Spanish (es_ES)** - Español
- **French (fr_FR)** - Français
- **German (de_DE)** - Deutsch

### For Users

#### Changing Language

1. Open the application
2. Go to **Settings** → **Language**
3. Select your preferred language
4. Restart the application for full language change

#### Locale-Specific Features

- **Number Formatting**: Numbers are formatted according to your locale
- **Date/Time Formatting**: Dates and times follow local conventions
- **Unit Systems**: Default unit systems are set based on your locale
- **Engineering Codes**: Relevant design codes are prioritized based on your region

### For Developers

#### Adding Translations to Your Plugin

1. **Mark Strings for Translation**:
   ```python
   # In your plugin code
   class MyPlugin(PluginBase):
       def create_ui(self):
           button = QPushButton(self._("Calculate"))
           label = QLabel(self._("Results"))
   ```

2. **Extract and Manage Translations**:
   ```bash
   # Extract translatable strings
   python src/eng_struct_tools/tools/i18n_cli.py extract

   # Create new locale
   python src/eng_struct_tools/tools/i18n_cli.py create-locale es_ES

   # Update translations
   python src/eng_struct_tools/tools/i18n_cli.py update

   # Compile translations
   python src/eng_struct_tools/tools/i18n_cli.py compile
   ```

#### Translation Management Tools

- **i18n CLI Tool**: `src/eng_struct_tools/tools/i18n_cli.py`
- **Setup Script**: `scripts/setup_i18n.py`
- **Update Script**: `scripts/update_translations.py`

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Contributing Translations

We especially welcome translation contributions! To contribute translations:

1. Check if your language is already supported
2. If not, create a new locale using the i18n tools
3. Translate the strings in the PO files
4. Test your translations
5. Submit a pull request

## License

This project is licensed under the AGPL License - see the [LICENSE](LICENSE) file for details.