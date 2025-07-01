"""
IFC utilities and wrapper functions for the Engineering Structural Tools.

This module provides a simplified interface for working with IFC files,
including reading, writing, and manipulating IFC data for structural engineering.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import uuid
from datetime import datetime

try:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.util.element
    import ifcopenshell.util.unit

    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    ifcopenshell = None


class IFCError(Exception):
    """Exception raised for IFC-related errors."""

    pass


class IFCManager:
    """
    Manages IFC file operations and provides a simplified interface.

    This class wraps ifcopenshell functionality to provide easier access
    to common IFC operations for structural engineering applications.
    """

    def __init__(self):
        """Initialize the IFC manager."""
        self.logger = logging.getLogger(__name__)

        if not IFC_AVAILABLE:
            self.logger.error("ifcopenshell is not available")
            raise IFCError("ifcopenshell library is required but not installed")

        self.model: Optional[ifcopenshell.file] = None
        self.file_path: Optional[Path] = None

        self.logger.info("IFC manager initialized")

    def create_new_model(self, schema: str = "IFC4") -> ifcopenshell.file:
        """
        Create a new IFC model.

        Args:
            schema: IFC schema version (e.g., "IFC4", "IFC2X3")

        Returns:
            New IFC model
        """
        try:
            self.model = ifcopenshell.file(schema=schema)
            self.file_path = None

            # Create basic project structure
            self._create_basic_structure()

            self.logger.info(f"Created new IFC model with schema {schema}")
            return self.model

        except Exception as e:
            self.logger.error(f"Failed to create new IFC model: {e}")
            raise IFCError(f"Cannot create new IFC model: {e}")

    def load_model(self, file_path: Union[str, Path]) -> ifcopenshell.file:
        """
        Load an IFC model from file.

        Args:
            file_path: Path to IFC file

        Returns:
            Loaded IFC model
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise IFCError(f"IFC file not found: {file_path}")

            self.model = ifcopenshell.open(str(file_path))
            self.file_path = file_path

            self.logger.info(f"Loaded IFC model from {file_path}")
            return self.model

        except Exception as e:
            self.logger.error(f"Failed to load IFC model: {e}")
            raise IFCError(f"Cannot load IFC model: {e}")

    def save_model(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save the IFC model to file.

        Args:
            file_path: Path to save file (uses current path if None)
        """
        if self.model is None:
            raise IFCError("No IFC model loaded")

        try:
            if file_path is not None:
                self.file_path = Path(file_path)

            if self.file_path is None:
                raise IFCError("No file path specified")

            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            self.model.write(str(self.file_path))
            self.logger.info(f"Saved IFC model to {self.file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save IFC model: {e}")
            raise IFCError(f"Cannot save IFC model: {e}")

    def _create_basic_structure(self) -> None:
        """Create basic IFC project structure."""
        if self.model is None:
            return

        try:
            # Create project
            project = ifcopenshell.api.run(
                "root.create_entity",
                self.model,
                ifc_class="IfcProject",
                name="Structural Engineering Project",
            )

            # Create units
            ifcopenshell.api.run(
                "unit.assign_unit",
                self.model,
                length={"is_metric": True, "raw": "MILLIMETRE"},
            )

            # Create site
            site = ifcopenshell.api.run(
                "root.create_entity", self.model, ifc_class="IfcSite", name="Site"
            )

            # Create building
            building = ifcopenshell.api.run(
                "root.create_entity",
                self.model,
                ifc_class="IfcBuilding",
                name="Building",
            )

            # Create building storey
            storey = ifcopenshell.api.run(
                "root.create_entity",
                self.model,
                ifc_class="IfcBuildingStorey",
                name="Ground Floor",
            )

            # Create spatial hierarchy
            ifcopenshell.api.run(
                "aggregate.assign_object",
                self.model,
                relating_object=project,
                related_object=site,
            )
            ifcopenshell.api.run(
                "aggregate.assign_object",
                self.model,
                relating_object=site,
                related_object=building,
            )
            ifcopenshell.api.run(
                "aggregate.assign_object",
                self.model,
                relating_object=building,
                related_object=storey,
            )

            self.logger.debug("Created basic IFC project structure")

        except Exception as e:
            self.logger.warning(f"Failed to create basic structure: {e}")

    def get_elements_by_type(self, ifc_type: str) -> List[Any]:
        """
        Get all elements of a specific IFC type.

        Args:
            ifc_type: IFC type name (e.g., "IfcBeam", "IfcColumn")

        Returns:
            List of IFC elements
        """
        if self.model is None:
            raise IFCError("No IFC model loaded")

        try:
            return self.model.by_type(ifc_type)
        except Exception as e:
            self.logger.error(f"Failed to get elements by type {ifc_type}: {e}")
            return []

    def get_element_by_guid(self, guid: str) -> Optional[Any]:
        """
        Get an element by its GUID.

        Args:
            guid: Element GUID

        Returns:
            IFC element or None if not found
        """
        if self.model is None:
            raise IFCError("No IFC model loaded")

        try:
            return self.model.by_guid(guid)
        except Exception as e:
            self.logger.error(f"Failed to get element by GUID {guid}: {e}")
            return None

    def create_structural_element(
        self, element_type: str, name: str, properties: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a structural element.

        Args:
            element_type: Type of element ("beam", "column", "footing", etc.)
            name: Element name
            properties: Optional properties dictionary

        Returns:
            Created IFC element
        """
        if self.model is None:
            raise IFCError("No IFC model loaded")

        try:
            # Map element types to IFC classes
            type_mapping = {
                "beam": "IfcBeam",
                "column": "IfcColumn",
                "footing": "IfcFooting",
                "slab": "IfcSlab",
                "wall": "IfcWall",
                "member": "IfcMember",
            }

            ifc_class = type_mapping.get(element_type.lower(), "IfcBuildingElement")

            # Create element
            element = ifcopenshell.api.run(
                "root.create_entity", self.model, ifc_class=ifc_class, name=name
            )

            # Add properties if provided
            if properties:
                self._add_properties_to_element(element, properties)

            self.logger.info(f"Created {element_type} element: {name}")
            return element

        except Exception as e:
            self.logger.error(f"Failed to create structural element: {e}")
            raise IFCError(f"Cannot create structural element: {e}")

    def _add_properties_to_element(
        self, element: Any, properties: Dict[str, Any]
    ) -> None:
        """Add properties to an IFC element."""
        try:
            # Create property set
            pset = ifcopenshell.api.run(
                "pset.add_pset",
                self.model,
                product=element,
                name="Structural_Properties",
            )

            # Add properties
            for prop_name, prop_value in properties.items():
                ifcopenshell.api.run(
                    "pset.edit_pset",
                    self.model,
                    pset=pset,
                    properties={prop_name: prop_value},
                )

        except Exception as e:
            self.logger.warning(f"Failed to add properties to element: {e}")

    def get_element_properties(self, element: Any) -> Dict[str, Any]:
        """
        Get properties of an IFC element.

        Args:
            element: IFC element

        Returns:
            Dictionary of properties
        """
        try:
            properties = {}

            # Get property sets
            psets = ifcopenshell.util.element.get_psets(element)

            for pset_name, pset_data in psets.items():
                for prop_name, prop_value in pset_data.items():
                    if prop_name not in ["id", "type"]:
                        properties[f"{pset_name}.{prop_name}"] = prop_value

            return properties

        except Exception as e:
            self.logger.error(f"Failed to get element properties: {e}")
            return {}

    def update_element_property(
        self,
        element: Any,
        property_name: str,
        value: Any,
        pset_name: str = "Structural_Properties",
    ) -> None:
        """
        Update a property of an IFC element.

        Args:
            element: IFC element
            property_name: Name of the property
            value: New property value
            pset_name: Property set name
        """
        try:
            # Get or create property set
            psets = ifcopenshell.util.element.get_psets(element)

            if pset_name in psets:
                pset = self.model.by_id(psets[pset_name]["id"])
            else:
                pset = ifcopenshell.api.run(
                    "pset.add_pset", self.model, product=element, name=pset_name
                )

            # Update property
            ifcopenshell.api.run(
                "pset.edit_pset",
                self.model,
                pset=pset,
                properties={property_name: value},
            )

            self.logger.debug(f"Updated property {property_name} = {value}")

        except Exception as e:
            self.logger.error(f"Failed to update element property: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current IFC model.

        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {"status": "No model loaded"}

        try:
            info = {
                "schema": self.model.schema,
                "file_path": str(self.file_path) if self.file_path else None,
                "element_count": len(self.model.by_type("IfcRoot")),
                "project_name": None,
                "units": {},
            }

            # Get project name
            projects = self.model.by_type("IfcProject")
            if projects:
                info["project_name"] = projects[0].Name

            # Get units
            try:
                units = ifcopenshell.util.unit.get_project_unit(
                    self.model, "LENGTHUNIT"
                )
                if units:
                    info["units"]["length"] = units.Name
            except:
                pass

            return info

        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {"status": "Error getting model info", "error": str(e)}

    def validate_model(self) -> Tuple[bool, List[str]]:
        """
        Validate the IFC model.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if self.model is None:
            return False, ["No model loaded"]

        issues = []

        try:
            # Check for required elements
            projects = self.model.by_type("IfcProject")
            if not projects:
                issues.append("No IfcProject found")

            # Check for units
            try:
                length_unit = ifcopenshell.util.unit.get_project_unit(
                    self.model, "LENGTHUNIT"
                )
                if not length_unit:
                    issues.append("No length unit defined")
            except:
                issues.append("Error checking units")

            # Additional validation can be added here

            is_valid = len(issues) == 0
            return is_valid, issues

        except Exception as e:
            self.logger.error(f"Model validation failed: {e}")
            return False, [f"Validation error: {e}"]


# Global IFC manager instance
ifc_manager = IFCManager() if IFC_AVAILABLE else None
