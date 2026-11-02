"""QT model for displaying and editing data."""

from __future__ import annotations

import abc
import copy
import csv
import dataclasses
import pathlib
import sys
import typing
import warnings
from functools import lru_cache
from itertools import islice
from typing import List, Any, Optional, Union, Dict, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
    from galatea.tsv import TableRow

from PySide6 import QtCore, QtQml

__all__ = ["TsvModel", "export_data", "load_tsv_model"]


@dataclasses.dataclass
class TSVReference:
    """A data class for storing references to tab-separated values files."""

    line_number: int
    column: int


@dataclasses.dataclass
class TsvElementData:
    """A data class for storing elements from tab-separated values files."""

    data: str
    source: Optional[TSVReference] = None


class TsvModel(QtCore.QAbstractTableModel):
    """A model for displaying and editing tab-separated values."""

    # modified_changed = QtCore.Signal()
    isEmpty_changed = QtCore.Signal()

    SourceRole = QtCore.Qt.UserRole + 1
    ObjectRole = SourceRole + 1

    def __init__(self, /, parent: QtCore.QObject | None = None) -> None:
        """Initialize the TsvModel."""
        super().__init__(parent)
        self.columns_order: List[str] = []
        self.rows: List[Dict[str, Optional[TsvElementData]]] = []
        self.loading: bool = False

    @QtCore.Property(bool, notify=isEmpty_changed)
    def isEmpty(self) -> bool:
        """Return whether the model is empty."""
        return len(self.rows) == 0

    def load_data(
        self, column_order: List[str], data: List[dict[str, str]]
    ) -> None:
        """Load data into the model."""
        warnings.warn("use load_tsv_model() instead", DeprecationWarning)
        starting = self.isEmpty
        self.beginResetModel()
        self.columns_order = column_order
        if len(data) > 0:
            self.rows = data
            self._original_rows = copy.deepcopy(data)
        else:
            self.rows.clear()
            self._original_rows.clear()
        self.endResetModel()
        # self.modified_changed.emit()
        if starting != self.isEmpty:
            self.isEmpty_changed.emit()

    def _compare_are_same(self, a: Any, b: Any) -> bool:
        if isinstance(a, TsvElementData):
            if isinstance(b, TsvElementData):
                res = a.data == b.data
            elif b is None:
                res = a.data.strip() == ""
            else:
                res = a.data == b
            if not res:
                print(f"Data elements are not the same: {a} != {b}")
            return res
        res = a == b
        if not res:
            print(f"Data elements are not the same: {a} != {b}")
        return res

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        /,
        role: int = QtCore.Qt.ItemDataRole.EditRole,
    ) -> bool:
        """Set data in the model."""
        if not index.isValid():
            return False
        data_element = self.rows[index.row()][
            self.columns_order[index.column()]
        ]
        if role == QtCore.Qt.ItemDataRole.EditRole or role == self.ObjectRole:
            if data_element is None:
                self.rows[index.row()][self.columns_order[index.column()]] = (
                    value
                    if role == self.ObjectRole
                    else TsvElementData(data=value)
                )
            else:
                data_element.data = value
            if not self.loading:
                self.dataChanged.emit(
                    index,
                    index,
                    [
                        QtCore.Qt.ItemDataRole.DisplayRole,
                        QtCore.Qt.ItemDataRole.EditRole,
                    ]
                    + ([self.ObjectRole] if role == self.ObjectRole else []),
                )
            return True
        if role == self.SourceRole:
            if (
                self.rows[index.row()][self.columns_order[index.column()]]
                is None
            ):
                warnings.warn("Cannot set source data for an empty cell")
                return False
            data_element.source = value
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
        for _ in range(count):
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
        row = self.rows[index.row()]
        if role in [
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
        ]:
            column_key = self.columns_order[index.column()]
            if element := row[column_key]:
                return element.data
            else:
                return None
        if role == self.ObjectRole:
            return row[self.columns_order[index.column()]]
        if role == QtCore.Qt.FontRole:
            print("role == QtCore.Qt.FontRole")
        if role == self.SourceRole:
            data = self.rows[index.row()][self.columns_order[index.column()]]
            if data is not None:
                return self.rows[index.row()][
                    self.columns_order[index.column()]
                ].source
            return None
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
        return len(self.rows)

    def roleNames(self):
        """Return the role names for the model."""
        roles = super().roleNames()
        roles[self.SourceRole] = b"source"
        roles[self.ObjectRole] = b"object"
        return roles

    def insertRows(  # noqa: D102
        self,
        row: int,
        count: int,
        /,
        parent: QModelIndex | QPersistentModelIndex = QtCore.QModelIndex(),
    ) -> bool:
        starting = copy.deepcopy(self.rows)
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            default_row: Dict[str, None] = dict.fromkeys(
                self.columns_order, None
            )
            self.rows.insert(row + i, default_row)
        self.endInsertRows()
        if starting != self.rows:
            self.isEmpty_changed.emit()
        return True

    def removeColumns(
        self,
        column: int,
        count: int,
        /,
        parent: QtCore.QModelIndex
        | QtCore.QPersistentModelIndex = QtCore.QModelIndex(),
    ) -> bool:
        """Remove columns from the model."""
        if 0 < column <= len(self.columns_order):
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        for _ in range(count):
            self.columns_order.pop(column)
        self.endRemoveColumns()
        return True

    def removeRows(
        self,
        row: int,
        count: int,
        /,
        parent: QtCore.QModelIndex
        | QtCore.QPersistentModelIndex = QtCore.QModelIndex(),
    ) -> bool:
        """Remove rows from model."""
        if 0 < row <= len(self.rows):
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            self.rows.pop(row)
        self.endRemoveRows()
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


def load_tsv_model(
    model: TsvModel, column_order: List[str], data: List[TableRow]
):
    """Load TSV data into the model."""
    while model.rowCount() > 0:
        model.removeRow(0)

    while model.columnCount() > 0:
        model.removeColumn(0)
    model.insertColumns(0, len(column_order))

    for column_index, column_name in enumerate(column_order):
        model.setHeaderData(
            column_index, QtCore.Qt.Orientation.Horizontal, column_name
        )
    model.insertRows(0, len(data))
    for row_index, row_data in enumerate(data):
        model.setHeaderData(
            row_index,
            QtCore.Qt.Orientation.Vertical,
            str(row_data.line_number),
        )
        for column_index, column_name in enumerate(column_order):
            model_index = model.index(row_index, column_index)
            value = row_data.entry.get(column_name)
            model.setData(
                model_index,
                TsvElementData(
                    data=value,
                    source=TSVReference(
                        line_number=row_data.line_number,
                        column=column_index + 1,
                    ),
                ),
                TsvModel.ObjectRole,
            )
    model.dataChanged.emit(
        model.index(0, 0),
        model.index(model.rowCount() - 1, model.columnCount() - 1),
        [
            model.SourceRole,
            QtCore.Qt.ItemDataRole.DisplayRole,
        ],
    )


@lru_cache
def read_data(file_path, dialect):
    print("reading file")
    with open(file_path, "r") as fp:
        reader = csv.reader(fp, dialect=dialect)
        return list(reader)


def _get_row(file_path, row, dialect):
    print(f"getting row {row}")
    start_index = row - 1
    end_index = start_index + 1
    with file_path.open("r", newline="", encoding="utf-8") as fp:
        csv_reader = csv.reader(fp, dialect=dialect or csv.excel_tab)
        return next(
            islice(
                csv_reader,
                start_index,
                end_index,
            ),
            None,
        )


QML_IMPORT_NAME = "galatea"
QML_IMPORT_MAJOR_VERSION = 1


def load_tsv_file_to_inspector(file, private_data, inspector: TsvInspector):
    private_data.file = file
    print("Cache cleared")
    private_data.tsv_rows.clear()
    inspector.fileChanged.emit(file)
    if not file.isValid():
        return

    file_path = pathlib.Path(file.toLocalFile())
    if not file_path.exists():
        return
    print(f"Reading file: {file_path}")
    inspector.state_object = TsvInspectorLoadingState(inspector, private_data)
    QtCore.QCoreApplication.processEvents()
    try:
        with file_path.open("r", newline="", encoding="utf-8") as fp:
            csv_reader = csv.reader(
                fp, dialect=private_data.dialect or csv.excel_tab
            )
            for row_id, row in enumerate(csv_reader):
                private_data.tsv_rows[row_id + 1] = row
            inspector.state_object = TsvInspectorLoadedState(
                inspector, private_data
            )
        inspector.dataChanged.emit()
    except Exception as e:
        print("unable to read file", file=sys.stderr)
        private_data.tsv_rows.clear()
        inspector.state_object = TsvInspectorEmptyState(
            inspector, private_data, e
        )
        raise e


@dataclasses.dataclass
class PrivateTsvInspectorData:
    file: QtCore.QUrl = QtCore.QUrl()
    dialect: typing.Optional[csv.Dialect] = None
    tsv_rows: typing.Dict[int, typing.List[str]] = dataclasses.field(
        default_factory=dict
    )


@QtQml.QmlElement
class TsvInspector(QtCore.QObject):
    fileChanged = QtCore.Signal(QtCore.QUrl)
    stateChanged = QtCore.Signal(str)
    dataChanged = QtCore.Signal()

    class TsvInspectorState(abc.ABC):
        def __init__(
            self, base: TsvInspector, private_data: PrivateTsvInspectorData
        ):
            self.base = base
            self.private_data = private_data

        def reload_file(self):
            pass

        @abc.abstractmethod
        def get_state_name(self) -> str:
            """Return the name of the state."""

        @abc.abstractmethod
        def set_file(self, file: QtCore.QUrl) -> None:
            """Set the file for the TSV inspector."""

        @abc.abstractmethod
        def set_dialect(self, dialect) -> None:
            """Set the dialect for the TSV inspector."""

        @abc.abstractmethod
        def value_is_different(
            self, value: str, tsv_line: int, tsv_column: int
        ) -> Optional[bool]:
            """Return True if the value is different from the one in the TSV file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._private_data = PrivateTsvInspectorData()
        self._state_object: TsvInspector.TsvInspectorState = (
            TsvInspectorEmptyState(self, self._private_data)
        )

    @QtCore.Slot("QVariant", result=bool)
    def entryHasChanged(self, value: TsvElementData) -> bool:
        if value is None:
            return True
        if value.source is None:
            return True
        res = self._state_object.value_is_different(
            value.data, value.source.line_number, value.source.column
        )
        return res is True or res is None

    @property
    def state_object(self) -> TsvInspector.TsvInspectorState:
        return self._state_object

    @state_object.setter
    def state_object(self, state_object: TsvInspector.TsvInspectorState):
        self._state_object = state_object
        self.stateChanged.emit(state_object.get_state_name())

    def get_current_state_name(self) -> str:
        return self._state_object.get_state_name()

    def set_dialect(self, dialect):
        self._state_object.set_dialect(dialect)

    def get_dialect(self):
        return self._private_data.dialect

    def set_file(self, file: QtCore.QUrl):
        self._state_object.set_file(file)

    def get_file(self):
        return self._private_data.file

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return self._state_object.value_is_different(
            value, tsv_line, tsv_column
        )

    @QtCore.Slot()
    def reloadFile(self):
        self._state_object.reload_file()

    @QtCore.Slot("QVariant", result=bool)
    def dataIsDifferent(self, value):
        if (
            self._private_data.file is None
            or self._private_data.file.isEmpty()
        ):
            return False
        file_path = pathlib.Path(self._private_data.file.toLocalFile())
        if not file_path.is_file():
            return False

        if value.columnCount() == 0 or value.rowCount() == 0:
            print("Value is empty")
            return False

        for row_id in range(value.rowCount()):
            index = value.index(row_id, 0)
            model_data = value.data(index, TsvModel.ObjectRole)
            if model_data is None:
                return True
            if model_data.source is None:
                return True
            tsv_row = self._private_data.tsv_rows.get(
                model_data.source.line_number
            )
            # tsv_row = self.tsv_rows.get(model_data.source.line_number)
            if not tsv_row:
                return True
            # print(f"checking row {row_id}")
            for column_id in range(value.columnCount()):
                index = value.index(row_id, column_id)
                model_data = value.data(index, TsvModel.ObjectRole)
                if model_data is None:
                    return True
                if model_data.source is None:
                    return True
                tsv_element = tsv_row[model_data.source.column - 1]
                if tsv_element != model_data.data:
                    return True
        return False

    state_name = QtCore.Property(
        str, get_current_state_name, notify=stateChanged
    )
    file = QtCore.Property(QtCore.QUrl, get_file, set_file, notify=fileChanged)
    dialect = QtCore.Property("QVariant", get_dialect, set_dialect)


class TsvInspectorLoadingState(TsvInspector.TsvInspectorState):
    def get_state_name(self) -> str:
        return "Loading"

    def set_file(self, file: QtCore.QUrl) -> None:
        print("Unable to set file while loading")

    def set_dialect(self, dialect) -> None:
        print("Unable to set file while loading")

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return None


class TsvInspectorLoadedState(TsvInspector.TsvInspectorState):
    def get_state_name(self) -> str:
        return "Loaded"

    def set_dialect(self, dialect) -> None:
        self.base.dialect = dialect

    def set_file(self, file: QtCore.QUrl) -> None:
        if file != self.private_data.file:
            load_tsv_file_to_inspector(file, self.private_data, self.base)

    def reload_file(self):
        load_tsv_file_to_inspector(
            self.private_data.file, self.private_data, self.base
        )

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        tsv_line_index = tsv_line
        tsv_column_index = tsv_column - 1
        tsv_value = self.private_data.tsv_rows[tsv_line_index][
            tsv_column_index
        ]
        return tsv_value != value


class TsvInspectorEmptyState(TsvInspector.TsvInspectorState):
    def get_state_name(self) -> str:
        return "Empty"

    def set_dialect(self, dialect) -> None:
        self.private_data.dialect = dialect

    def set_file(self, file: QtCore.QUrl):
        if file != self.private_data.file:
            load_tsv_file_to_inspector(file, self.private_data, self.base)
        self.base.state_object = TsvInspectorLoadedState(
            self.base, self.private_data
        )

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return True
