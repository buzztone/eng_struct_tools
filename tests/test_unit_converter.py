"""
Unit tests for the UnitConverter class.

This module contains tests for unit conversion functionality
including conversions between different unit systems and validation.
"""

import pytest
from unittest.mock import patch, Mock

from src.eng_struct_tools.shared_libs.unit_converter import UnitConverter, UnitSystem


class TestUnitSystem:
    """Test cases for UnitSystem class."""
    
    def test_initialization(self):
        """Test UnitSystem initialization."""
        units = {"length": "m", "force": "N"}
        system = UnitSystem("Test System", units)
        
        assert system.name == "Test System"
        assert system.units == units
    
    def test_get_unit(self):
        """Test getting units from system."""
        units = {"length": "m", "force": "N"}
        system = UnitSystem("Test System", units)
        
        assert system.get_unit("length") == "m"
        assert system.get_unit("force") == "N"
        assert system.get_unit("nonexistent") == "dimensionless"
    
    def test_string_representation(self):
        """Test string representation of UnitSystem."""
        system = UnitSystem("Test System", {})
        assert str(system) == "UnitSystem(Test System)"


class TestUnitConverter:
    """Test cases for UnitConverter class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = UnitConverter()
    
    def test_initialization(self):
        """Test UnitConverter initialization."""
        assert self.converter is not None
        assert self.converter.current_system == "SI_Engineering"
        assert hasattr(self.converter, 'ureg')
        assert len(self.converter.UNIT_SYSTEMS) > 0
    
    def test_predefined_unit_systems(self):
        """Test that predefined unit systems are available."""
        systems = self.converter.UNIT_SYSTEMS
        
        # Check that expected systems exist
        assert "SI" in systems
        assert "SI_Engineering" in systems
        assert "Imperial" in systems
        assert "Imperial_Engineering" in systems
        
        # Check system properties
        si_system = systems["SI"]
        assert si_system.name == "SI (Metric)"
        assert si_system.get_unit("length") == "m"
        assert si_system.get_unit("force") == "N"
        
        si_eng_system = systems["SI_Engineering"]
        assert si_eng_system.get_unit("length") == "mm"
        assert si_eng_system.get_unit("stress") == "MPa"
    
    def test_get_current_system(self):
        """Test getting current unit system."""
        current = self.converter.get_current_system()
        assert isinstance(current, UnitSystem)
        assert current.name == "SI Engineering"
    
    def test_set_current_system(self):
        """Test setting current unit system."""
        # Set to valid system
        self.converter.set_current_system("Imperial")
        assert self.converter.current_system == "Imperial"
        
        # Test invalid system
        with pytest.raises(ValueError):
            self.converter.set_current_system("NonexistentSystem")
    
    def test_get_available_systems(self):
        """Test getting list of available systems."""
        systems = self.converter.get_available_systems()
        assert isinstance(systems, list)
        assert len(systems) >= 4
        assert "SI" in systems
        assert "Imperial" in systems
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_convert(self, mock_ureg):
        """Test unit conversion."""
        # Mock the pint registry
        mock_quantity = Mock()
        mock_quantity.to.return_value.magnitude = 1000.0
        mock_ureg.Quantity.return_value = mock_quantity
        
        # Test conversion
        result = self.converter.convert(1.0, "m", "mm")
        
        # Verify pint was called correctly
        mock_ureg.Quantity.assert_called_once_with(1.0, "m")
        mock_quantity.to.assert_called_once_with("mm")
        assert result == 1000.0
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_convert_error_handling(self, mock_ureg):
        """Test error handling in unit conversion."""
        # Mock pint to raise an exception
        mock_ureg.Quantity.side_effect = Exception("Invalid unit")
        
        with pytest.raises(ValueError):
            self.converter.convert(1.0, "invalid_unit", "m")
    
    def test_convert_to_system(self):
        """Test converting to specific unit system."""
        # Mock the convert method
        with patch.object(self.converter, 'convert', return_value=1000.0) as mock_convert:
            result = self.converter.convert_to_system(1.0, "m", "length", "SI_Engineering")
            
            # Should call convert with target unit from system
            mock_convert.assert_called_once_with(1.0, "m", "mm")
            assert result == 1000.0
    
    def test_convert_to_system_invalid(self):
        """Test converting to invalid unit system."""
        with pytest.raises(ValueError):
            self.converter.convert_to_system(1.0, "m", "length", "InvalidSystem")
    
    def test_get_unit_for_quantity(self):
        """Test getting unit for quantity type."""
        # Test with current system
        unit = self.converter.get_unit_for_quantity("length")
        assert unit == "mm"  # SI_Engineering default
        
        # Test with specific system
        unit = self.converter.get_unit_for_quantity("length", "SI")
        assert unit == "m"
        
        # Test with invalid system
        with pytest.raises(ValueError):
            self.converter.get_unit_for_quantity("length", "InvalidSystem")
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_validate_unit(self, mock_ureg):
        """Test unit validation."""
        # Mock successful parsing
        mock_ureg.parse_expression.return_value = Mock()
        assert self.converter.validate_unit("m") is True
        
        # Mock failed parsing
        mock_ureg.parse_expression.side_effect = Exception("Invalid")
        assert self.converter.validate_unit("invalid_unit") is False
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_get_unit_dimensions(self, mock_ureg):
        """Test getting unit dimensions."""
        # Mock successful parsing
        mock_quantity = Mock()
        mock_quantity.dimensionality = "[length]"
        mock_ureg.parse_expression.return_value = mock_quantity
        
        dimensions = self.converter.get_unit_dimensions("m")
        assert dimensions == "[length]"
        
        # Mock failed parsing
        mock_ureg.parse_expression.side_effect = Exception("Invalid")
        dimensions = self.converter.get_unit_dimensions("invalid")
        assert dimensions == "unknown"
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_are_units_compatible(self, mock_ureg):
        """Test checking unit compatibility."""
        # Mock compatible units
        mock_q1 = Mock()
        mock_q1.dimensionality = "[length]"
        mock_q2 = Mock()
        mock_q2.dimensionality = "[length]"
        mock_ureg.parse_expression.side_effect = [mock_q1, mock_q2]
        
        assert self.converter.are_units_compatible("m", "mm") is True
        
        # Mock incompatible units
        mock_q2.dimensionality = "[mass]"
        mock_ureg.parse_expression.side_effect = [mock_q1, mock_q2]
        
        assert self.converter.are_units_compatible("m", "kg") is False
        
        # Mock parsing error
        mock_ureg.parse_expression.side_effect = Exception("Invalid")
        assert self.converter.are_units_compatible("invalid1", "invalid2") is False
    
    @patch('src.eng_struct_tools.shared_libs.unit_converter.ureg')
    def test_format_value_with_unit(self, mock_ureg):
        """Test formatting value with unit."""
        # Mock quantity
        mock_quantity = Mock()
        mock_quantity.units = Mock()
        mock_quantity.units.__format__ = Mock(return_value="mm")
        mock_ureg.Quantity.return_value = mock_quantity
        
        formatted = self.converter.format_value_with_unit(1000.0, "mm", 2)
        assert "1000.00" in formatted
        assert "mm" in formatted
        
        # Mock error case
        mock_ureg.Quantity.side_effect = Exception("Invalid")
        formatted = self.converter.format_value_with_unit(1000.0, "invalid", 2)
        assert formatted == "1000.00 invalid"
    
    def test_get_common_units_for_quantity(self):
        """Test getting common units for quantity types."""
        # Test length units
        length_units = self.converter.get_common_units_for_quantity("length")
        assert isinstance(length_units, list)
        assert "mm" in length_units
        assert "m" in length_units
        assert "ft" in length_units
        
        # Test force units
        force_units = self.converter.get_common_units_for_quantity("force")
        assert "N" in force_units
        assert "kN" in force_units
        assert "lbf" in force_units
        
        # Test unknown quantity
        unknown_units = self.converter.get_common_units_for_quantity("unknown")
        assert unknown_units == []
    
    def test_unit_system_completeness(self):
        """Test that all unit systems have required quantity types."""
        required_quantities = [
            "length", "area", "volume", "force", "moment", "stress",
            "pressure", "density", "mass", "time", "temperature"
        ]
        
        for system_name, system in self.converter.UNIT_SYSTEMS.items():
            for quantity in required_quantities:
                unit = system.get_unit(quantity)
                assert unit != "dimensionless", f"System {system_name} missing {quantity}"
    
    def test_setup_aliases(self):
        """Test that unit aliases are set up correctly."""
        # This is tested indirectly through the initialization
        # The _setup_aliases method should not raise exceptions
        converter = UnitConverter()
        assert converter is not None
    
    def test_global_instance(self):
        """Test that global unit converter instance is available."""
        from src.eng_struct_tools.shared_libs.unit_converter import unit_converter
        assert unit_converter is not None
        assert isinstance(unit_converter, UnitConverter)
