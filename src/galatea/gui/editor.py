"""QQml based tsv Editor."""

import argparse
import importlib.resources
import sys

import galatea

from PySide6.QtQuickControls2 import QQuickStyle
from PySide6 import QtCore, QtGui, QtQml
from typing import List, Any, Optional, Union, Dict

__all__ = []


class Model(QtCore.QAbstractTableModel):
    def __init__(self, /, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.columns_order: List[str] = []
        self._rows: List[Dict[str, str]] = []

    def load_data(self, data: List[dict[str, str]]) -> None:
        if len(data) > 0:
            self.columns_order = list(data[0].keys())
            self._rows = data

    def columnCount(
        self,
        parent: Optional[
            Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]
        ] = None,
    ) -> int:
        return len(self.columns_order)

    def flags(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, /
    ) -> QtCore.Qt.ItemFlag:
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def data(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        /,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        if role in [
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
        ]:
            if 0 < index.row() >= len(self._rows):
                return None
            row = self._rows[index.row()]
            if 0 < index.column() > (len(self.columns_order) - 1):
                return None
            column_key = self.columns_order[index.column()]
            return row[column_key]
            # return self._rows[index.row()].get(, None)
        return None

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self.columns_order[section]
        return super().headerData(section, orientation, role)

    def rowCount(
        self,
        parent: Optional[
            QtCore.QModelIndex | QtCore.QPersistentModelIndex
        ] = None,
    ) -> int:
        return len(self._rows)

    def roleNames(self):
        return {QtCore.Qt.DisplayRole: b"display", QtCore.Qt.EditRole: b"edit"}


def get_qt_style():
    match sys.platform:
        case "win32":
            return "Windows"
        case "darwin":
            return "macOS"
    return "Fusion"


def load_tsv(path):
    m = Model()
    with open(path, "r", encoding="utf-8") as input_tsv_fp:
        input_tsv_dialect = galatea.tsv.get_tsv_dialect(input_tsv_fp)
    rows = []
    for row in galatea.tsv.iter_tsv_file(path, dialect=input_tsv_dialect):
        rows.append(row.entry)
    m.load_data(rows)
    return m


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("tsv", type=str, help="tsv file path")
    return parser


def main():
    args = get_arg_parser().parse_args()
    qt_style = get_qt_style()
    QQuickStyle.setStyle(qt_style)
    print("Compiled Qt Version:", QtCore.__version__)

    app = QtGui.QGuiApplication()
    engine = QtQml.QQmlApplicationEngine()

    entry_point = importlib.resources.files("galatea.gui").joinpath(
        "qml/Editor/App.qml"
    )
    component = QtQml.QQmlComponent(
        engine, QtCore.QUrl.fromLocalFile(str(entry_point))
    )
    tsv_model = load_tsv(args.tsv)
    root_object = component.createWithInitialProperties({
        "windowTitle": "Metadata Editor with Python backend",
        "model": tsv_model,
    })

    if not root_object:
        print("unable to load qml application")
        return -1
    return app.exec()


if __name__ == "__main__":
    main()
