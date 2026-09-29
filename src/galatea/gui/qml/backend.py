"""Python QML backend."""

from __future__ import annotations

import csv
import logging
import pathlib
import sys
from typing import (
    Type,
    Union,
    List,
    Dict,
    TYPE_CHECKING,
    Protocol,
    TextIO,
    Callable,
    Tuple,
)
import galatea.tsv
from PySide6 import QtCore

from galatea.utils import GalateaException
from galatea.gui.qml import models

if TYPE_CHECKING:
    from galatea.tsv import TableRow, IterTsvFileProtocol

module_logger = logging.getLogger("QML")
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s"
    )
)
module_logger.addHandler(console_handler)
module_logger.setLevel(logging.DEBUG)
__all__ = ["Backend"]


def get_first_row_of_tsv(
    path: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    tsv_reader_strategy=csv.reader,
):
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = tsv_reader_strategy(f, dialect=dialect)
        return next(reader)


def load_tsv(
    path: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    model: models.TsvModel,
    read_tsv_rows_strategy: IterTsvFileProtocol = galatea.tsv.iter_tsv_file,
):
    rows: List[Dict[str, str]] = []
    row: TableRow[Dict[str, str]]
    _rows = list(read_tsv_rows_strategy(path, dialect=dialect))
    for row in _rows:
        rows.append(row.entry)
    if len(rows) > 0:
        columns_headings = list(rows[0].keys())
    else:
        columns_headings = get_first_row_of_tsv(path, dialect)
    model.load_data(columns_headings, rows)


def get_tsv_dialect(
    path: pathlib.Path, detection_strategy=galatea.tsv.get_tsv_dialect
) -> Union[Type[csv.Dialect], csv.Dialect]:
    with path.open("r", encoding="utf-8") as fp:
        return detection_strategy(fp)


class Backend(QtCore.QObject):
    """Backend for the Galatea QML application."""

    class LoadTsvProtocol(Protocol):
        """Load a TSV file into a model."""

        def __call__(
            self,
            path: pathlib.Path,
            dialect: Union[Type[csv.Dialect], csv.Dialect],
            model: models.TsvModel,
        ) -> None:
            """Load a TSV file into a model.

            Args:
                path: Path to the TSV file.
                dialect: Dialect of the TSV file.
                model: Model to load the TSV file into.

            Returns:
                None
            """

    class WriteTsvProtocol(Protocol):
        """Write a TSV file from a model."""

        def __call__(
            self,
            file_name: pathlib.Path,
            headings: List[str],
            data: List[Dict[str, str]],
            dialect: Union[Type[csv.Dialect], csv.Dialect],
            writing_strategy: Callable[
                [
                    TextIO,
                    List[str],
                    List[Dict[str, str]],
                    Union[Type[csv.Dialect], csv.Dialect],
                ],
                None,
            ],
        ):
            """Write a TSV file from a model.

            Args:
                file_name: The path to the file to write.
                headings: The headings to write on the first line.
                data: The data to write. Dictionary of that keys matches the
                    headings.
                dialect: The tsv dialect to use.
                writing_strategy: The strategy to use to write the data.

            Returns:
                None

            """

    class GetTSVDialectProtocol(Protocol):
        """Get the dialect to use for a file."""

        def __call__(
            self, path: pathlib.Path
        ) -> Union[Type[csv.Dialect], csv.Dialect]:
            """Get the dialect to use for a file.

            Args:
                path: The path to the file.

            Returns:
                The dialect to use for the file.
            """

    class ExportModelDataProtocol(Protocol):
        """Export data from a model."""

        def __call__(
            self, model: QtCore.QAbstractTableModel
        ) -> Tuple[List[str], List[Dict[str, str]]]:
            """Export data from a model.

            Args:
                model: The model to export data from.

            Returns:
                A tuple of the headings and the data. The headings are a list
                    of strings and the data is a list of dictionaries where
                    each dictionary has a string key and a string value.
            """

    logSubmitted = QtCore.Signal(str)
    # logSubmitted is called from QML to pass logging message to backend.

    load_tsv_strategy: LoadTsvProtocol = load_tsv
    save_tsv_strategy: WriteTsvProtocol = galatea.tsv.write_tsv_file2
    export_model_data_strategy: ExportModelDataProtocol = models.export_data
    get_dialect_strategy: GetTSVDialectProtocol = get_tsv_dialect

    @QtCore.Slot(QtCore.QUrl, "QVariant", "QVariant", result=bool)
    def load_model_from_file(
        self,
        file_path: QtCore.QUrl,
        dialect: Union[Type[csv.Dialect], csv.Dialect],
        tsv_model: models.TsvModel,
    ) -> bool:
        """Load the model from the given file path using the given dialect."""
        try:
            Backend.load_tsv_strategy(
                pathlib.Path(file_path.path()),
                dialect,
                tsv_model,
            )
            return True
        except GalateaException as error:
            module_logger.exception(
                'Unable to open file "%s". Reason: %s', file_path.path(), error
            )
            return False

    @QtCore.Slot(QtCore.QUrl, "QVariant", "QVariant", result=bool)
    def save_model_to_file(
        self,
        file_path: QtCore.QUrl,
        dialect: csv.Dialect,
        tsv_model: models.TsvModel,
    ):
        """Save the given model using the given dialect."""
        module_logger.info(f"Running saveModelToFile {file_path.path()}")
        headers, data = Backend.export_model_data_strategy(tsv_model)
        Backend.save_tsv_strategy(
            pathlib.Path(file_path.path()),
            headings=headers,
            data=data,
            dialect=dialect,
        )
        return True

    @QtCore.Slot(QtCore.QUrl, result="QVariant")
    def get_dialect(
        self, file_path: QtCore.QUrl
    ) -> Union[Type[csv.Dialect], csv.Dialect]:
        """Return the dialect of the file at the given path."""
        return Backend.get_dialect_strategy(pathlib.Path(file_path.path()))
