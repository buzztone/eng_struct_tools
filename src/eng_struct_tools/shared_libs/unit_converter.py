"""
Unit conversion and management for the Engineering Structural Tools.

This module provides comprehensive unit conversion capabilities using the
pint library, with predefined unit systems for structural engineering.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
import pint

# Initialize pint unit registry
ureg = pint.UnitRegistry()
ureg.default_format = "~P"  # Pretty format


class UnitSystem:
    """
    Represents a consistent unit system for structural engineering.
    """

    def __init__(self, name: str, units: Dict[str, str]):
        """
        Initialize a unit system.

        Args:
            name: Name of the unit system
            units: Dictionary mapping quantity types to unit strings
        """
        self.name = name
        self.units = units

    def get_unit(self, quantity_type: str) -> str:
        """Get the unit for a specific quantity type."""
        return self.units.get(quantity_type, "dimensionless")

    def __str__(self) -> str:
        return f"UnitSystem({self.name})"


class UnitConverter:
    """
    Handles unit conversions and management for structural engineering calculations.

    This class provides methods for converting between different unit systems,
    validating units, and managing unit preferences.
    """

    # Predefined unit systems
    UNIT_SYSTEMS = {
        "SI": UnitSystem(
            "SI (Metric)",
            {
                "length": "m",
                "area": "m²",
                "volume": "m³",
                "force": "N",
                "moment": "N⋅m",
                "stress": "Pa",
                "pressure": "Pa",
                "density": "kg/m³",
                "mass": "kg",
                "time": "s",
                "temperature": "°C",
                "angle": "rad",
                "frequency": "Hz",
                "velocity": "m/s",
                "acceleration": "m/s²",
            },
        ),
        "SI_Engineering": UnitSystem(
            "SI Engineering",
            {
                "length": "mm",
                "area": "mm²",
                "volume": "mm³",
                "force": "N",
                "moment": "N⋅mm",
                "stress": "MPa",
                "pressure": "MPa",
                "density": "kg/m³",
                "mass": "kg",
                "time": "s",
                "temperature": "°C",
                "angle": "rad",
                "frequency": "Hz",
                "velocity": "mm/s",
                "acceleration": "mm/s²",
            },
        ),
        "Imperial": UnitSystem(
            "Imperial (US)",
            {
                "length": "ft",
                "area": "ft²",
                "volume": "ft³",
                "force": "lbf",
                "moment": "lbf⋅ft",
                "stress": "psi",
                "pressure": "psi",
                "density": "lb/ft³",
                "mass": "lb",
                "time": "s",
                "temperature": "°F",
                "angle": "rad",
                "frequency": "Hz",
                "velocity": "ft/s",
                "acceleration": "ft/s²",
            },
        ),
        "Imperial_Engineering": UnitSystem(
            "Imperial Engineering",
            {
                "length": "in",
                "area": "in²",
                "volume": "in³",
                "force": "lbf",
                "moment": "lbf⋅in",
                "stress": "ksi",
                "pressure": "ksi",
                "density": "lb/in³",
                "mass": "lb",
                "time": "s",
                "temperature": "°F",
                "angle": "rad",
                "frequency": "Hz",
                "velocity": "in/s",
                "acceleration": "in/s²",
            },
        ),
    }

    def __init__(self, default_system: str = "SI_Engineering"):
        """
        Initialize the unit converter.

        Args:
            default_system: Default unit system name
        """
        self.logger = logging.getLogger(__name__)
        self.current_system = default_system
        self.ureg = ureg

        # Unit aliases for common engineering units
        self._setup_aliases()

        self.logger.info(f"Unit converter initialized with {default_system} system")

    def _setup_aliases(self) -> None:
        """Set up unit aliases for common engineering units."""
        try:
            # Define common aliases
            self.ureg.define("ksi = 1000 * psi")
            self.ureg.define("ksf = 1000 * psf")
            self.ureg.define("pcf = pound / foot**3")
            self.ureg.define("psf = pound * force / foot**2")

        except Exception as e:
            self.logger.warning(f"Some unit aliases may already exist: {e}")

    def get_current_system(self) -> UnitSystem:
        """Get the current unit system."""
        return self.UNIT_SYSTEMS[self.current_system]

    def set_current_system(self, system_name: str) -> None:
        """
        Set the current unit system.

        Args:
            system_name: Name of the unit system
        """
        if system_name not in self.UNIT_SYSTEMS:
            raise ValueError(f"Unknown unit system: {system_name}")

        self.current_system = system_name
        self.logger.info(f"Unit system changed to {system_name}")

    def get_available_systems(self) -> List[str]:
        """Get list of available unit system names."""
        return list(self.UNIT_SYSTEMS.keys())

    def convert(
        self, value: Union[float, int, Decimal], from_unit: str, to_unit: str
    ) -> float:
        """
        Convert a value from one unit to another.

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted value
        """
        try:
            # Create quantity with source unit
            quantity = self.ureg.Quantity(value, from_unit)

            # Convert to target unit
            converted = quantity.to(to_unit)

            return float(converted.magnitude)

        except Exception as e:
            self.logger.error(
                f"Unit conversion failed: {value} {from_unit} -> {to_unit}: {e}"
            )
            raise ValueError(f"Cannot convert {from_unit} to {to_unit}: {e}")

    def convert_to_system(
        self,
        value: Union[float, int, Decimal],
        from_unit: str,
        quantity_type: str,
        target_system: Optional[str] = None,
    ) -> float:
        """
        Convert a value to the unit of a specific quantity type in a unit system.

        Args:
            value: Value to convert
            from_unit: Source unit
            quantity_type: Type of quantity (e.g., 'length', 'force')
            target_system: Target unit system (uses current if None)

        Returns:
            Converted value
        """
        if target_system is None:
            target_system = self.current_system

        if target_system not in self.UNIT_SYSTEMS:
            raise ValueError(f"Unknown unit system: {target_system}")

        target_unit = self.UNIT_SYSTEMS[target_system].get_unit(quantity_type)
        return self.convert(value, from_unit, target_unit)

    def get_unit_for_quantity(
        self, quantity_type: str, system: Optional[str] = None
    ) -> str:
        """
        Get the unit for a quantity type in a specific system.

        Args:
            quantity_type: Type of quantity
            system: Unit system (uses current if None)

        Returns:
            Unit string
        """
        if system is None:
            system = self.current_system

        if system not in self.UNIT_SYSTEMS:
            raise ValueError(f"Unknown unit system: {system}")

        return self.UNIT_SYSTEMS[system].get_unit(quantity_type)

    def validate_unit(self, unit_string: str) -> bool:
        """
        Validate if a unit string is recognized.

        Args:
            unit_string: Unit string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            self.ureg.parse_expression(unit_string)
            return True
        except Exception:
            return False

    def get_unit_dimensions(self, unit_string: str) -> str:
        """
        Get the dimensions of a unit.

        Args:
            unit_string: Unit string

        Returns:
            Dimension string
        """
        try:
            quantity = self.ureg.parse_expression(unit_string)
            return str(quantity.dimensionality)
        except Exception as e:
            self.logger.error(f"Cannot get dimensions for unit {unit_string}: {e}")
            return "unknown"

    def are_units_compatible(self, unit1: str, unit2: str) -> bool:
        """
        Check if two units are dimensionally compatible.

        Args:
            unit1: First unit
            unit2: Second unit

        Returns:
            True if compatible, False otherwise
        """
        try:
            q1 = self.ureg.parse_expression(unit1)
            q2 = self.ureg.parse_expression(unit2)
            return q1.dimensionality == q2.dimensionality
        except Exception:
            return False

    def format_value_with_unit(
        self, value: Union[float, int, Decimal], unit: str, precision: int = 3
    ) -> str:
        """
        Format a value with its unit for display.

        Args:
            value: Numerical value
            unit: Unit string
            precision: Number of decimal places

        Returns:
            Formatted string
        """
        try:
            quantity = self.ureg.Quantity(value, unit)
            return f"{value:.{precision}f} {quantity.units:~P}"
        except Exception:
            return f"{value:.{precision}f} {unit}"

    def get_common_units_for_quantity(self, quantity_type: str) -> List[str]:
        """
        Get common units for a quantity type.

        Args:
            quantity_type: Type of quantity

        Returns:
            List of common unit strings
        """
        common_units = {
            "length": ["mm", "cm", "m", "km", "in", "ft", "yd", "mile"],
            "area": ["mm²", "cm²", "m²", "km²", "in²", "ft²", "yd²"],
            "volume": ["mm³", "cm³", "m³", "in³", "ft³", "yd³"],
            "force": ["N", "kN", "MN", "lbf", "kip"],
            "moment": ["N⋅mm", "N⋅m", "kN⋅m", "lbf⋅in", "lbf⋅ft", "kip⋅ft"],
            "stress": ["Pa", "kPa", "MPa", "GPa", "psi", "ksi"],
            "pressure": ["Pa", "kPa", "MPa", "psi", "psf"],
            "density": ["kg/m³", "g/cm³", "lb/ft³", "lb/in³"],
            "mass": ["g", "kg", "tonne", "lb", "ton"],
            "temperature": ["°C", "°F", "K"],
            "angle": ["rad", "deg", "grad"],
            "velocity": ["m/s", "km/h", "ft/s", "mph"],
            "acceleration": ["m/s²", "ft/s²", "g"],
        }

        return common_units.get(quantity_type, [])


# Global unit converter instance
unit_converter = UnitConverter()
