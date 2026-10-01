"""QT model for displaying and editing data."""

from __future__ import annotations

import copy
import typing
from typing import List, Any, Optional, Union, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt

from PySide6 import QtCore


class TsvModel(QtCore.QAbstractTableModel):
    """A model for displaying and editing tab-separated values."""

    modified_changed = QtCore.Signal()
    isEmpty_changed = QtCore.Signal()

    def __init__(self, /, parent: QtCore.QObject | None = None) -> None:
        """Initialize the TsvModel."""
        super().__init__(parent)
        self.columns_order: List[str] = []
        self._rows: List[Dict[str, str]] = []
        self._original_rows: List[Dict[str, str]] = []
        self.dataChanged.connect(self.get_changes)

    def get_changes(self):
        """Yield changes in the model since it was loaded."""
        for current_data, original_data in zip(
            self._rows, self._original_rows
        ):
            if current_data != original_data:
                yield (current_data, original_data)

    @QtCore.Property(bool, notify=isEmpty_changed)
    def isEmpty(self) -> bool:
        """Return whether the model is empty."""
        return len(self._rows) == 0

    @QtCore.Property(bool, notify=modified_changed)
    def isModified(self) -> bool:
        """Return whether the model has been modified since first loaded."""
        for _ in self.get_changes():
            return True
        return False

    def load_data(
        self, column_order: List[str], data: List[dict[str, str]]
    ) -> None:
        """Load data into the model."""
        starting = self.isEmpty
        self.beginResetModel()
        self.columns_order = column_order
        if len(data) > 0:
            self._rows = data
            self._original_rows = copy.deepcopy(data)
        else:
            self._rows.clear()
            self._original_rows.clear()
        self.endResetModel()
        self.modified_changed.emit()
        if starting != self.isEmpty:
            self.isEmpty_changed.emit()

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        /,
        role: int = QtCore.Qt.ItemDataRole.EditRole,
    ) -> bool:
        """Set data in the model."""
        if role == QtCore.Qt.ItemDataRole.EditRole:
            starting = self.isModified
            self._rows[index.row()][self.columns_order[index.column()]] = value
            self.dataChanged.emit(index, index)
            if starting != self.isModified:
                self.modified_changed.emit()
            return True
        return super().setData(index, value, role)

    def columnCount(
        self,
        parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None,
    ) -> int:
        """Return the number of columns in the model.

        This uses the length of the internals columns_order data to determine
        the number of columns.
        """
        return len(self.columns_order)

    def insertColumns(  # noqa: D102
        self,
        column: int,
        count: int,
        /,
        parent: QModelIndex | QPersistentModelIndex = QtCore.QModelIndex(),
    ) -> bool:
        self.beginInsertColumns(parent, column, column + count - 1)
        self.columns_order.insert(column, None)
        self.endInsertColumns()
        return True

    def setHeaderData(  # noqa: D102
        self,
        section: int,
        orientation: Qt.Orientation,
        value: typing.Any,
        /,
        role: int = QtCore.Qt.ItemDataRole.EditRole,
    ) -> bool:
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if len(self.columns_order) < section + 1:
                return False

            if role == QtCore.Qt.ItemDataRole.EditRole:
                self.columns_order[section] = value
                return True

        return False

    def flags(
        self, index: QModelIndex | QPersistentModelIndex, /
    ) -> QtCore.Qt.ItemFlag:
        """Return the flags for the given index."""
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        /,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the data for the given index and role.

        This uses the member variables _rows and columns_order to determine
        the data for the given index and role.
        """
        if not index.isValid():
            return None
        if role in [
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
        ]:
            row = self._rows[index.row()]
            column_key = self.columns_order[index.column()]
            return row[column_key]
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the header data for the given section and orientation.

        This uses the member variable columns_order to determine the
        horizontal header data for the given section and orientation.
        """
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self.columns_order[section] or section + 1
        return super().headerData(section, orientation, role)

    def rowCount(
        self,
        parent: Optional[QModelIndex | QPersistentModelIndex] = None,
    ) -> int:
        """Return the number of rows in the model.

        This uses the length of the internals _rows data to determine the
        number of rows.
        """
        return len(self._rows)

    def roleNames(self):
        """Return the role names for the model."""
        return {QtCore.Qt.DisplayRole: b"display", QtCore.Qt.EditRole: b"edit"}

    def insertRows(  # noqa: D102
        self,
        row: int,
        count: int,
        /,
        parent: QModelIndex | QPersistentModelIndex = QtCore.QModelIndex(),
    ) -> bool:
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            default_row = {k: None for k in self.columns_order}
            self._rows.insert(row + i, default_row)
        self.endInsertRows()
        return True


def export_data(
    model: QtCore.QAbstractTableModel,
) -> Tuple[List[str], List[Dict[str, str]]]:
    """Export data from a QAbstractTableModel to a list of dictionaries."""
    column_order = []
    data_data = []
    column_count = model.columnCount()

    for column_index in range(column_count):
        column_order.append(
            model.headerData(column_index, QtCore.Qt.Orientation.Horizontal)
        )

    for row_index in range(model.rowCount()):
        row = {}
        for column_index in range(column_count):
            row[
                model.headerData(
                    column_index, QtCore.Qt.Orientation.Horizontal
                )
            ] = model.data(model.index(row_index, column_index))
        data_data.append(row)
    return column_order, data_data
