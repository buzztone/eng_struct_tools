"""
Common UI widgets and utilities for the Engineering Structural Tools.

This module provides reusable UI components that can be used across
different plugins and the core application.
"""

from typing import Optional, List, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QSizePolicy,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor


class StatusWidget(QWidget):
    """
    Status widget for displaying plugin and application status.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the status widget."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                padding: 2px 5px;
            }
        """
        )
        layout.addWidget(self.status_label)

    def set_status(self, message: str, color: str = "#2c3e50") -> None:
        """
        Set the status message and color.

        Args:
            message: Status message
            color: Text color (CSS color string)
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                padding: 2px 5px;
            }}
        """
        )


class LabeledInput(QWidget):
    """
    Widget combining a label with an input field.
    """

    # Signal emitted when value changes
    valueChanged = pyqtSignal(object)

    def __init__(
        self, label: str, input_type: str = "text", parent: Optional[QWidget] = None
    ):
        """
        Initialize the labeled input.

        Args:
            label: Label text
            input_type: Type of input ('text', 'double', 'int', 'combo')
            parent: Parent widget
        """
        super().__init__(parent)
        self.input_type = input_type
        self._setup_ui(label)

    def _setup_ui(self, label: str) -> None:
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)

        # Input widget based on type
        if self.input_type == "text":
            self.input_widget = QLineEdit()
            self.input_widget.textChanged.connect(
                lambda: self.valueChanged.emit(self.get_value())
            )
        elif self.input_type == "double":
            self.input_widget = QDoubleSpinBox()
            self.input_widget.setRange(-999999.0, 999999.0)
            self.input_widget.setDecimals(3)
            self.input_widget.valueChanged.connect(
                lambda: self.valueChanged.emit(self.get_value())
            )
        elif self.input_type == "int":
            self.input_widget = QSpinBox()
            self.input_widget.setRange(-999999, 999999)
            self.input_widget.valueChanged.connect(
                lambda: self.valueChanged.emit(self.get_value())
            )
        elif self.input_type == "combo":
            self.input_widget = QComboBox()
            self.input_widget.currentTextChanged.connect(
                lambda: self.valueChanged.emit(self.get_value())
            )
        else:
            self.input_widget = QLineEdit()

        layout.addWidget(self.input_widget)

    def get_value(self) -> Any:
        """Get the current value."""
        if self.input_type == "text":
            return self.input_widget.text()
        elif self.input_type in ["double", "int"]:
            return self.input_widget.value()
        elif self.input_type == "combo":
            return self.input_widget.currentText()
        return None

    def set_value(self, value: Any) -> None:
        """Set the value."""
        if self.input_type == "text":
            self.input_widget.setText(str(value))
        elif self.input_type in ["double", "int"]:
            self.input_widget.setValue(value)
        elif self.input_type == "combo":
            self.input_widget.setCurrentText(str(value))

    def set_items(self, items: List[str]) -> None:
        """Set combo box items (only for combo type)."""
        if self.input_type == "combo":
            self.input_widget.clear()
            self.input_widget.addItems(items)

    def set_range(self, minimum: float, maximum: float) -> None:
        """Set range for numeric inputs."""
        if self.input_type in ["double", "int"]:
            self.input_widget.setRange(minimum, maximum)


class ParameterGroup(QGroupBox):
    """
    Group box for organizing related parameters.
    """

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        """
        Initialize the parameter group.

        Args:
            title: Group title
            parent: Parent widget
        """
        super().__init__(title, parent)
        self.parameters: Dict[str, LabeledInput] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.layout = QFormLayout(self)
        self.layout.setSpacing(8)

    def add_parameter(
        self,
        name: str,
        label: str,
        input_type: str = "text",
        default_value: Any = None,
        items: Optional[List[str]] = None,
        range_values: Optional[tuple] = None,
    ) -> LabeledInput:
        """
        Add a parameter to the group.

        Args:
            name: Parameter name (key)
            label: Display label
            input_type: Input type
            default_value: Default value
            items: Items for combo box
            range_values: (min, max) for numeric inputs

        Returns:
            The created LabeledInput widget
        """
        param_widget = LabeledInput(label, input_type)

        if items and input_type == "combo":
            param_widget.set_items(items)

        if range_values and input_type in ["double", "int"]:
            param_widget.set_range(range_values[0], range_values[1])

        if default_value is not None:
            param_widget.set_value(default_value)

        self.parameters[name] = param_widget
        self.layout.addRow(param_widget)

        return param_widget

    def get_values(self) -> Dict[str, Any]:
        """Get all parameter values."""
        return {name: widget.get_value() for name, widget in self.parameters.items()}

    def set_values(self, values: Dict[str, Any]) -> None:
        """Set parameter values."""
        for name, value in values.items():
            if name in self.parameters:
                self.parameters[name].set_value(value)

    def get_parameter(self, name: str) -> Optional[LabeledInput]:
        """Get a specific parameter widget."""
        return self.parameters.get(name)


class ResultsTable(QTableWidget):
    """
    Table widget for displaying calculation results.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the results table."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the table."""
        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Configure headers
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.verticalHeader().setVisible(False)

        # Style
        self.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """
        )

    def set_data(
        self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None
    ) -> None:
        """
        Set table data.

        Args:
            data: List of dictionaries containing row data
            headers: Optional list of column headers
        """
        if not data:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        # Determine headers
        if headers is None:
            headers = list(data[0].keys())

        # Set table dimensions
        self.setRowCount(len(data))
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Populate data
        for row, row_data in enumerate(data):
            for col, header in enumerate(headers):
                value = row_data.get(header, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, col, item)

    def add_row(self, row_data: Dict[str, Any]) -> None:
        """Add a single row to the table."""
        if self.columnCount() == 0:
            return

        headers = [
            self.horizontalHeaderItem(i).text() for i in range(self.columnCount())
        ]

        row = self.rowCount()
        self.insertRow(row)

        for col, header in enumerate(headers):
            value = row_data.get(header, "")
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)

    def clear_data(self) -> None:
        """Clear all table data."""
        self.setRowCount(0)


class ProgressDialog(QWidget):
    """
    Progress dialog for long-running operations.
    """

    def __init__(self, title: str = "Processing...", parent: Optional[QWidget] = None):
        """
        Initialize the progress dialog.

        Args:
            title: Dialog title
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Cancel button (optional)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button)

        self.setFixedSize(300, 120)

    def set_progress(self, value: int, message: str = "") -> None:
        """
        Set progress value and message.

        Args:
            value: Progress value (0-100)
            message: Status message
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def set_indeterminate(self, indeterminate: bool = True) -> None:
        """Set indeterminate progress mode."""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
