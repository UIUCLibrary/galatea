"""QT model for displaying and editing data."""

from __future__ import annotations

import abc
import copy
import csv
import dataclasses
import logging
import pathlib
import sys
import typing
import warnings
from typing import List, Any, Optional, Dict, Tuple, TYPE_CHECKING

from csv import Dialect

if TYPE_CHECKING:
    from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
    from galatea.tsv import TableRow

from PySide6 import QtCore
from PySide6.QtCore import QUrl, QObject, Slot, QAbstractTableModel

from PySide6.QtQml import QmlElement

__all__ = ["TsvModel", "export_data", "load_tsv_model"]

logger = logging.getLogger(__name__)

QML_IMPORT_NAME = "Galatea"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


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


def is_model_modified(
    model: TsvModel,
    index: QModelIndex | QPersistentModelIndex,
    inspector: Optional[TsvInspector] = None,
) -> bool:
    if inspector is None:
        return True
    if inspector.state_name == "Loading":
        return False
    return inspector.entryHasChanged(
        model.data(index, role=TsvModel.ObjectRole)
    )


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


def _iter_tsv(file_path, dialect):
    with file_path.open("r", newline="", encoding="utf-8") as fp:
        csv_reader = csv.reader(fp, dialect=dialect or csv.excel_tab)
        for row_id, row in enumerate(csv_reader):
            yield row_id + 1, row


def model_is_empty(model: QtCore.QAbstractTableModel) -> bool:
    if model.columnCount() == 0 or model.rowCount() == 0:
        return True
    return False


def compare_tsv_model_to_data_rows(
    model: TsvModel, rows: Dict[int, List[str]]
) -> bool:
    if model_is_empty(model):
        print("Value is empty")
        return False

    for row_id in range(model.rowCount()):
        index = model.index(row_id, 0)
        model_data = model.data(index, TsvModel.ObjectRole)
        if any([model_data is None, model_data.source is None]):
            return True
        tsv_row = rows.get(model_data.source.line_number)
        if not tsv_row:
            return True

        for column_id in range(model.columnCount()):
            index = model.index(row_id, column_id)
            model_data = model.data(index, TsvModel.ObjectRole)
            if any([model_data is None, model_data.source is None]):
                return True
            tsv_element = tsv_row[model_data.source.column - 1]
            if tsv_element != model_data.data:
                return True
    return False


@dataclasses.dataclass
class PrivateTsvInspectorData:
    file: QtCore.QUrl = QtCore.QUrl()
    dialect: typing.Optional[csv.Dialect] = None
    tsv_rows: typing.Dict[int, typing.List[str]] = dataclasses.field(
        default_factory=dict
    )


class TsvInspectorState(abc.ABC):
    def __init__(
        self,
        base: TsvInspector,
        private_data: Optional[PrivateTsvInspectorData] = None,
    ):
        self.base = base
        self.private_data = private_data or PrivateTsvInspectorData()

    def reload_file(self):
        """Reload current file.

        This defaults to a noop.
        """

    @abc.abstractmethod
    def get_state_name(self) -> str:
        """Return the name of the state."""

    @abc.abstractmethod
    def set_file(self, file: QtCore.QUrl) -> None:
        """Set the file for the TSV inspector."""

    @abc.abstractmethod
    def set_dialect(self, dialect) -> None:
        """Set the dialect for the TSV inspector."""

    def get_dialect(self):
        return self.private_data.dialect

    @abc.abstractmethod
    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        """Return True if the value is different from the one in the TSV file."""


@QmlElement
class TsvInspector(QObject):
    fileChanged = QtCore.Signal(QtCore.QUrl)
    stateChanged = QtCore.Signal(str)
    dataChanged = QtCore.Signal()

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self._private_data = PrivateTsvInspectorData(**kwargs)
        self._state_object: TsvInspectorState = TsvInspectorEmptyState(
            self, self._private_data
        )

    @Slot(TsvElementData, result=bool)
    def entryHasChanged(
        self, value: TsvElementData, compare_strategy=None
    ) -> bool:
        if value is None:
            return True
        if value.source is None:
            return True
        res = (compare_strategy or self._state_object.value_is_different)(
            value.data, value.source.line_number, value.source.column
        )
        return res is True or res is None

    @property
    def state_object(self) -> TsvInspectorState:
        return self._state_object

    @state_object.setter
    def state_object(self, state_object: TsvInspectorState):
        self._state_object = state_object
        self.stateChanged.emit(state_object.get_state_name())

    def get_current_state_name(self) -> str:
        return self._state_object.get_state_name()

    def get_dialect(self):
        return self._state_object.get_dialect()

    def set_dialect(self, dialect):
        self._state_object.set_dialect(dialect)

    def get_file(self, strategy=None):
        return strategy(self) if strategy else self._state_object.get_file

    def set_file(self, file_: QtCore.QUrl, strategy=None):
        (strategy or self._state_object.set_file)(file_)

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int, compare_strategy=None
    ) -> Optional[bool]:
        return (compare_strategy or self._state_object.value_is_different)(
            value, tsv_line, tsv_column
        )

    @Slot()
    def reloadFile(self, strategy=None):
        (strategy or self._state_object.reload_file)()

    @Slot("QVariant", result=bool)
    def dataIsDifferent(
        self, value: TsvModel, compare_strategy=compare_tsv_model_to_data_rows
    ) -> bool:
        if (
            self._private_data.file is None
            or self._private_data.file.isEmpty()
        ):
            return False
        file_path = pathlib.Path(self._private_data.file.toLocalFile())
        if not file_path.is_file():
            return False
        return compare_strategy(value, self._private_data.tsv_rows)

    state_name = QtCore.Property(
        str, get_current_state_name, notify=stateChanged
    )
    dialect = QtCore.Property(Dialect, get_dialect, set_dialect)
    file = QtCore.Property(QUrl, get_file, set_file, notify=fileChanged)


@QmlElement
class TsvModel(QAbstractTableModel):
    """A model for displaying and editing tab-separated values."""

    isEmpty_changed = QtCore.Signal()
    inspectorChanged = QtCore.Signal()

    SourceRole = QtCore.Qt.ItemDataRole.UserRole + 1
    ObjectRole = SourceRole + 1
    IsModifiedRole = ObjectRole + 1

    check_modified_strategy: typing.Callable[
        [
            TsvModel,
            QModelIndex | QPersistentModelIndex,
            Optional[TsvInspector],
        ],
        bool,
    ] = is_model_modified

    def __init__(self, /, parent: QtCore.QObject | None = None) -> None:
        """Initialize the TsvModel."""
        super().__init__(parent)
        self.columns_order: List[str] = []
        self.rows: List[Dict[str, Optional[TsvElementData]]] = []
        self.loading: bool = False
        self._inspector: Optional[TsvInspector] = None

    # @QtCore.Property(bool, notify=isEmpty_changed)
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

    def _set_data(self, index, value, role):
        data_element = self.rows[index.row()][
            self.columns_order[index.column()]
        ]
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
                    self.IsModifiedRole,
                ]
                + ([self.ObjectRole] if role == self.ObjectRole else []),
            )
        return True

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

        if role == QtCore.Qt.ItemDataRole.EditRole or role == self.ObjectRole:
            return self._set_data(index, value, role)
        if role == self.SourceRole:
            if (
                self.rows[index.row()][self.columns_order[index.column()]]
                is None
            ):
                warnings.warn("Cannot set source data for an empty cell")
                return False
            if data_element := self.rows[index.row()][
                self.columns_order[index.column()]
            ]:
                data_element.source = value
                return True
        return super().setData(index, value, role)

    def columnCount(
        self,
        parent: Optional[QModelIndex | QPersistentModelIndex] = None,
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
            self.columns_order.insert(column, "")
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

    def _is_modified(self, index: QModelIndex | QPersistentModelIndex) -> bool:
        return True

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
        if role == self.IsModifiedRole:
            return TsvModel.check_modified_strategy(
                self, index, self._inspector
            )
        if role == self.SourceRole:
            data = self.rows[index.row()][self.columns_order[index.column()]]
            if data is not None:
                if item := self.rows[index.row()][
                    self.columns_order[index.column()]
                ]:
                    return item.source
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
        roles[self.IsModifiedRole] = b"isModified"
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
            default_row: Dict[str, Optional[TsvElementData]] = dict.fromkeys(
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

    def _get_inspector(self) -> Optional[TsvInspector]:
        return self._inspector

    def _set_inspector(self, inspector: TsvInspector) -> None:
        changed = self._inspector != inspector
        if changed:
            self._inspector = inspector
            self.inspectorChanged.emit()

    inspector = QtCore.Property(
        TsvInspector, _get_inspector, _set_inspector, notify=inspectorChanged
    )


class TsvInspectorLoadingState(TsvInspectorState):
    def get_state_name(self) -> str:
        return "Loading"

    def set_file(self, file: QtCore.QUrl) -> None:
        logger.error("Unable to set file while loading")

    def set_dialect(self, dialect) -> None:
        logger.error("Unable to set file while loading")

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return None


def load_tsv_file_to_inspector(
    file: QtCore.QUrl,
    private_data: PrivateTsvInspectorData,
    inspector: TsvInspector,
    iter_tsv_data_strategy=_iter_tsv,
) -> None:
    private_data.file = file
    private_data.tsv_rows.clear()
    inspector.fileChanged.emit(file)
    if not file.isValid():
        return

    file_path = pathlib.Path(file.toLocalFile())
    if not file_path.exists():
        return
    inspector.state_object = TsvInspectorLoadingState(inspector, private_data)
    QtCore.QCoreApplication.processEvents()
    try:
        for row_id, row_data in iter_tsv_data_strategy(
            file_path, private_data.dialect
        ):
            private_data.tsv_rows[row_id] = row_data
        inspector.state_object = TsvInspectorLoadedState(
            inspector, private_data
        )
        inspector.dataChanged.emit()
    except Exception as e:
        print("unable to read file", file=sys.stderr)
        private_data.tsv_rows.clear()
        inspector.state_object = TsvInspectorEmptyState(
            inspector, private_data
        )
        raise e


def compare_value(expected_value, line_number: int, column: int, rows) -> bool:
    tsv_line_index = line_number
    tsv_column_index = column - 1
    tsv_value = rows[tsv_line_index][tsv_column_index]
    return tsv_value != expected_value


class TsvInspectorLoadedState(TsvInspectorState):
    load_tsv_file_to_inspector_strategy = load_tsv_file_to_inspector
    compare_value_strategy = compare_value

    def get_state_name(self) -> str:
        return "Loaded"

    def set_dialect(self, dialect) -> None:
        self.private_data.dialect = dialect

    def set_file(self, file: QtCore.QUrl) -> None:
        if file != self.private_data.file:
            TsvInspectorLoadedState.load_tsv_file_to_inspector_strategy(
                file, self.private_data, self.base
            )

    def reload_file(self):
        TsvInspectorLoadedState.load_tsv_file_to_inspector_strategy(
            self.private_data.file, self.private_data, self.base
        )

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return TsvInspectorLoadedState.compare_value_strategy(
            value, tsv_line, tsv_column, self.private_data.tsv_rows
        )


class TsvInspectorEmptyState(TsvInspectorState):
    load_tsv_file_strategy = load_tsv_file_to_inspector

    def get_state_name(self) -> str:
        return "Empty"

    def set_dialect(self, dialect) -> None:
        self.private_data.dialect = dialect

    def set_file(self, file: QtCore.QUrl):
        if file != self.private_data.file:
            TsvInspectorEmptyState.load_tsv_file_strategy(
                file, self.private_data, self.base
            )
        self.base.state_object = TsvInspectorLoadedState(
            self.base, self.private_data
        )

    def value_is_different(
        self, value: str, tsv_line: int, tsv_column: int
    ) -> Optional[bool]:
        return True
