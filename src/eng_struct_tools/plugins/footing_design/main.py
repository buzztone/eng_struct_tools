"""
Main module for the Footing Design Plugin.

This module contains the main plugin class that implements the footing
design functionality according to the plugin architecture.
"""

import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QSplitter,
)
from PyQt6.QtCore import Qt

from ...core_app.plugin_base import DesignPlugin, PluginInfo, MenuItem, HostAPI
from ...shared_libs.common_ui_widgets import (
    ParameterGroup,
    ResultsTable,
    ProgressDialog,
)
from ...shared_libs.unit_converter import unit_converter


class FootingDesignWidget(QWidget):
    """
    Main widget for the footing design plugin.

    This widget provides the user interface for inputting footing parameters,
    running calculations, and displaying results.
    """

    def __init__(self, plugin_instance, parent: Optional[QWidget] = None):
        """
        Initialize the footing design widget.

        Args:
            plugin_instance: Reference to the plugin instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.plugin = plugin_instance
        self.logger = logging.getLogger(__name__)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Create splitter for input and output areas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Input parameters
        input_panel = self._create_input_panel()
        splitter.addWidget(input_panel)

        # Right panel - Results and output
        output_panel = self._create_output_panel()
        splitter.addWidget(output_panel)

        # Set splitter proportions
        splitter.setSizes([400, 600])

        # Control buttons
        button_layout = QHBoxLayout()

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        )
        button_layout.addWidget(self.calculate_button)

        self.clear_button = QPushButton("Clear")
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        self.export_button = QPushButton("Export Results")
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)

    def _create_input_panel(self) -> QWidget:
        """Create the input parameters panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Loads group
        self.loads_group = ParameterGroup("Applied Loads")
        self.loads_group.add_parameter(
            "axial_load", "Axial Load (N)", "double", 1000000.0, range_values=(0, 1e9)
        )
        self.loads_group.add_parameter(
            "moment_x", "Moment X (N⋅mm)", "double", 0.0, range_values=(-1e12, 1e12)
        )
        self.loads_group.add_parameter(
            "moment_y", "Moment Y (N⋅mm)", "double", 0.0, range_values=(-1e12, 1e12)
        )
        self.loads_group.add_parameter(
            "shear_x", "Shear X (N)", "double", 0.0, range_values=(-1e9, 1e9)
        )
        self.loads_group.add_parameter(
            "shear_y", "Shear Y (N)", "double", 0.0, range_values=(-1e9, 1e9)
        )
        layout.addWidget(self.loads_group)

        # Geometry group
        self.geometry_group = ParameterGroup("Footing Geometry")
        self.geometry_group.add_parameter(
            "length", "Length (mm)", "double", 2000.0, range_values=(100, 10000)
        )
        self.geometry_group.add_parameter(
            "width", "Width (mm)", "double", 2000.0, range_values=(100, 10000)
        )
        self.geometry_group.add_parameter(
            "thickness", "Thickness (mm)", "double", 500.0, range_values=(100, 2000)
        )
        layout.addWidget(self.geometry_group)

        # Material properties group
        self.material_group = ParameterGroup("Material Properties")
        self.material_group.add_parameter(
            "concrete_strength",
            "Concrete Strength (MPa)",
            "double",
            25.0,
            range_values=(10, 100),
        )
        self.material_group.add_parameter(
            "steel_strength",
            "Steel Strength (MPa)",
            "double",
            500.0,
            range_values=(200, 800),
        )
        self.material_group.add_parameter(
            "cover", "Cover (mm)", "double", 50.0, range_values=(20, 100)
        )
        layout.addWidget(self.material_group)

        # Soil properties group
        self.soil_group = ParameterGroup("Soil Properties")
        self.soil_group.add_parameter(
            "bearing_capacity",
            "Bearing Capacity (MPa)",
            "double",
            0.2,
            range_values=(0.05, 2.0),
        )
        self.soil_group.add_parameter(
            "unit_weight", "Unit Weight (kN/m³)", "double", 18.0, range_values=(10, 25)
        )
        layout.addWidget(self.soil_group)

        # Design code group
        self.code_group = ParameterGroup("Design Code")
        self.code_group.add_parameter(
            "design_code",
            "Design Code",
            "combo",
            "ACI 318",
            items=["ACI 318", "Eurocode 2", "AS 3600", "CSA A23.3"],
        )
        layout.addWidget(self.code_group)

        layout.addStretch()
        return panel

    def _create_output_panel(self) -> QWidget:
        """Create the output/results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Results table
        self.results_table = ResultsTable()
        layout.addWidget(self.results_table)

        # Calculation log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """
        )
        layout.addWidget(self.log_text)

        return panel

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.calculate_button.clicked.connect(self._run_calculation)
        self.clear_button.clicked.connect(self._clear_inputs)
        self.export_button.clicked.connect(self._export_results)

    def _run_calculation(self) -> None:
        """Run the footing design calculation."""
        try:
            # Get input values
            input_data = self._get_input_data()

            # Validate inputs
            is_valid, errors = self.plugin.validate_input(input_data)
            if not is_valid:
                self._log_message("Validation errors:")
                for error in errors:
                    self._log_message(f"  - {error}")
                return

            # Show progress
            self.plugin.host_api.show_progress(True)
            self.plugin.host_api.set_progress(10)

            # Run calculation
            self._log_message("Starting footing design calculation...")
            results = self.plugin.run_design(input_data)

            # Display results
            self._display_results(results)

            self.plugin.host_api.set_progress(100)
            self.plugin.host_api.show_progress(False)

            self._log_message("Calculation completed successfully.")

        except Exception as e:
            self.plugin.host_api.show_progress(False)
            self._log_message(f"Calculation failed: {e}")
            self.logger.error(f"Calculation error: {e}")

    def _get_input_data(self) -> Dict[str, Any]:
        """Get input data from the UI."""
        data = {}

        # Get values from all parameter groups
        data.update(self.loads_group.get_values())
        data.update(self.geometry_group.get_values())
        data.update(self.material_group.get_values())
        data.update(self.soil_group.get_values())
        data.update(self.code_group.get_values())

        return data

    def _display_results(self, results: Dict[str, Any]) -> None:
        """Display calculation results."""
        # Convert results to table format
        table_data = []

        for category, values in results.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    table_data.append(
                        {
                            "Category": category,
                            "Parameter": key,
                            "Value": (
                                f"{value:.3f}"
                                if isinstance(value, (int, float))
                                else str(value)
                            ),
                            "Unit": self._get_unit_for_parameter(key),
                        }
                    )
            else:
                table_data.append(
                    {
                        "Category": "General",
                        "Parameter": category,
                        "Value": (
                            f"{values:.3f}"
                            if isinstance(values, (int, float))
                            else str(values)
                        ),
                        "Unit": self._get_unit_for_parameter(category),
                    }
                )

        self.results_table.set_data(table_data)

    def _get_unit_for_parameter(self, parameter: str) -> str:
        """Get the appropriate unit for a parameter."""
        unit_map = {
            "area": "mm²",
            "stress": "MPa",
            "force": "N",
            "moment": "N⋅mm",
            "length": "mm",
            "pressure": "MPa",
        }

        # Simple mapping based on parameter name
        for key, unit in unit_map.items():
            if key in parameter.lower():
                return unit

        return ""

    def _clear_inputs(self) -> None:
        """Clear all input fields."""
        # Reset to default values
        self.loads_group.set_values(
            {
                "axial_load": 1000000.0,
                "moment_x": 0.0,
                "moment_y": 0.0,
                "shear_x": 0.0,
                "shear_y": 0.0,
            }
        )

        self.geometry_group.set_values(
            {"length": 2000.0, "width": 2000.0, "thickness": 500.0}
        )

        self.material_group.set_values(
            {"concrete_strength": 25.0, "steel_strength": 500.0, "cover": 50.0}
        )

        self.soil_group.set_values({"bearing_capacity": 0.2, "unit_weight": 18.0})

        self.results_table.clear_data()
        self.log_text.clear()

        self._log_message("Inputs cleared.")

    def _export_results(self) -> None:
        """Export results to file."""
        # TODO: Implement export functionality
        self._log_message("Export functionality not yet implemented.")

    def _log_message(self, message: str) -> None:
        """Add a message to the calculation log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")


class FootingDesignPlugin(DesignPlugin):
    """
    Footing design plugin for structural engineering calculations.

    This plugin provides comprehensive footing design capabilities including
    bearing capacity checks, reinforcement design, and code compliance verification.
    """

    def __init__(self):
        """Initialize the footing design plugin."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_plugin_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            name="Footing Design",
            version="0.1.0",
            description="Concrete footing design and analysis tool",
            author="Neil Murray",
            category="Structural Design",
            dependencies=["numpy", "matplotlib"],
        )

    def initialize(self, host_api: HostAPI) -> bool:
        """Initialize the plugin with host API access."""
        try:
            self.host_api = host_api
            self._is_initialized = True

            self.logger.info("Footing design plugin initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize footing design plugin: {e}")
            return False

    def get_menu_items(self) -> List[MenuItem]:
        """Get menu items for this plugin."""
        return [
            MenuItem(
                name="Design Footing",
                callback=self._show_design_interface,
                tooltip="Open footing design interface",
            )
        ]

    def create_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create the main widget for this plugin."""
        return FootingDesignWidget(self, parent)

    def _show_design_interface(self) -> None:
        """Show the footing design interface."""
        # This will be called when the menu item is clicked
        # The plugin manager will handle showing the widget
        pass

    def run_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the footing design calculation.

        Args:
            input_data: Input parameters for the design

        Returns:
            Design results dictionary
        """
        try:
            # TODO: Implement actual footing design calculations
            # For now, return mock results

            results = {
                "bearing_check": {
                    "applied_pressure": input_data["axial_load"]
                    / (input_data["length"] * input_data["width"]),
                    "allowable_pressure": input_data["bearing_capacity"]
                    * 1e6,  # Convert MPa to Pa
                    "utilization": (
                        input_data["axial_load"]
                        / (input_data["length"] * input_data["width"])
                    )
                    / (input_data["bearing_capacity"] * 1e6),
                },
                "reinforcement": {
                    "main_steel_area": 2000.0,  # mm²
                    "distribution_steel_area": 1500.0,  # mm²
                    "bar_spacing": 200.0,  # mm
                },
                "dimensions": {
                    "effective_depth": input_data["thickness"]
                    - input_data["cover"]
                    - 10,  # Assuming 20mm bar
                    "area": input_data["length"] * input_data["width"],
                },
            }

            self.design_results = results
            return results

        except Exception as e:
            self.logger.error(f"Design calculation failed: {e}")
            raise

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate input data for the design.

        Args:
            input_data: Input data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required parameters
        required_params = [
            "axial_load",
            "length",
            "width",
            "thickness",
            "concrete_strength",
            "bearing_capacity",
        ]

        for param in required_params:
            if param not in input_data:
                errors.append(f"Missing required parameter: {param}")
            elif input_data[param] <= 0:
                errors.append(f"Parameter {param} must be positive")

        # Check geometric constraints
        if "length" in input_data and "width" in input_data:
            if input_data["length"] < input_data["width"]:
                errors.append("Length should be greater than or equal to width")

        # Check bearing pressure
        if all(
            p in input_data
            for p in ["axial_load", "length", "width", "bearing_capacity"]
        ):
            applied_pressure = input_data["axial_load"] / (
                input_data["length"] * input_data["width"]
            )
            allowable_pressure = (
                input_data["bearing_capacity"] * 1e6
            )  # Convert MPa to Pa

            if applied_pressure > allowable_pressure:
                errors.append("Applied bearing pressure exceeds allowable capacity")

        return len(errors) == 0, errors

    def check_design_codes(self) -> List[str]:
        """Get list of supported design codes."""
        return ["ACI 318", "Eurocode 2", "AS 3600", "CSA A23.3"]
