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