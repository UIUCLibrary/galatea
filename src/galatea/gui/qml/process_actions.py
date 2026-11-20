"""Processing actions."""

import abc
import functools
import logging
from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, cast, Mapping

import shiboken6
from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QmlElement, QJSValue

from galatea import clean_tsv, modifiers
from galatea.gui.qml.error_handling import ProcessingActionError
from galatea.gui.qml.models import TsvModel

QML_IMPORT_NAME = "Galatea"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

__all__ = ["CleanAction", "JSProcessAction"]


@QmlElement
class ProcessingAction(QObject):
    modelChanged = QtCore.Signal()
    actionNameChanged = QtCore.Signal()
    reportGenerated = QtCore.Signal(str)
    progressChanged = QtCore.Signal(float)
    actionLogged = QtCore.Signal(str, int)

    def log_action(self, action_name: str, level: int = logging.INFO) -> None:
        self.actionLogged.emit(action_name, level)

    def submit_report(self, message: str) -> None:
        self._report = message
        self.reportGenerated.emit(message)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._model: TsvModel = TsvModel()
        self._action_name: str | None = None
        self._report = ""
        self.settings = {}

    def _get_model(self) -> TsvModel | None:
        return self._model

    def set_model(self, model: TsvModel) -> None:
        self._model = model

    def _set_action_name(self, name: str) -> None:
        self._action_name = name

    def get_action_name(self):
        return self._action_name

    def run(self):
        if shiboken6.isValid(self):
            self.process_data()
        else:
            raise RuntimeError("ProcessingAction was already deleted")

    def get_report(self):
        return self._report

    @abc.abstractmethod
    def process_data(self) -> None:
        """Process model data."""

    model = QtCore.Property(
        TsvModel, _get_model, set_model, notify=modelChanged
    )
    actionName = QtCore.Property(
        str,
        get_action_name,
        _set_action_name,
        notify=actionNameChanged,
        final=True,
    )
    report = QtCore.Property(str, get_report)


def use_header_data_to_get_headers(model: TsvModel) -> List[str]:
    return [
        model.headerData(column, QtCore.Qt.Orientation.Horizontal)
        for column in range(model.columnCount())
    ]


def get_row_modifier(
    action: ProcessingAction, **settings
) -> clean_tsv.RowTransformer:
    characters_to_remove = settings.get("charactersToRemove", "")
    transformer = clean_tsv.RowTransformer()
    column_names = []
    for col_index, header_value in enumerate(
        CleanAction.get_tsv_headers_strategy(cast(TsvModel, action.model))
    ):
        column_names.append(header_value)
    functions = []

    if settings.get("removeDoubleDashPostfix", False):
        functions.append(modifiers.remove_double_dash_postfix)

    if settings.get("removeTrailingPeriods", False):
        functions.append(modifiers.remove_trailing_periods)

    if settings.get("addCommaAfterSpace", False):
        functions.append(modifiers.add_comma_after_space)

    for character in characters_to_remove:
        functions.append(
            functools.partial(modifiers.remove_character, character=character)
        )
    if settings.get("removeTrailingPunctuation", False):
        functions.append(modifiers.remove_trailing_punctuation)
    transformer.add_transformation(
        condition=lambda k, v: k in column_names,
        transformation=lambda entry: modifiers.split_and_modify(
            entry,
            funcs=functions,
        ),
    )

    if settings.get("removeDupValues", False):
        transformer.add_transformation(modifiers.remove_duplicates)

    return transformer


def report_columns_update_in_each_row(
    rows_affected: Dict[int, List[str]],
) -> str:
    report_header = f"Cleaned data. {len(rows_affected)} rows updated."
    row_report_lines = []
    for line_number, affected_columns in rows_affected.items():
        affected_column_report = ", ".join([
            f'"{column_heading}"' for column_heading in affected_columns
        ])
        row_report_lines.append(f" * {line_number}: {affected_column_report}")
    rows_report = "\n".join(row_report_lines)
    return "\n".join([
        report_header,
        "The following line were affected",
        rows_report,
    ])


@QmlElement
class CleanAction(ProcessingAction):
    """Clean action for processing TSV data."""

    get_tsv_headers_strategy = use_header_data_to_get_headers
    get_row_modifier_strategy = get_row_modifier
    report_strategy = report_columns_update_in_each_row

    actionNameChanged = QtCore.Signal()

    def get_action_name(self) -> str:
        """Get the action name which is clean."""
        return "clean"

    @classmethod
    def iter_row(cls, model: TsvModel) -> Iterable[Tuple[int, Dict[str, str]]]:
        """Iterate over all rows affected by this action."""
        total_rows = model.rowCount()
        for row in range(total_rows):
            yield (
                row,
                {
                    heading: model.data(model.index(row, column_index))
                    for column_index, heading in enumerate(
                        cls.get_tsv_headers_strategy(model)
                    )
                },
            )

    @classmethod
    def iter_new_row_data(
        cls,
        model: TsvModel,
        row: int,
        row_data: Mapping[str, str],
        modifier: clean_tsv.RowTransformer,
    ):
        """Modify and iterate over data for given action."""
        result = modifier.transform(row_data)
        for k, updated_value in result.items():
            if result[k] == row_data[k]:
                continue
            try:
                column_number = cls.get_tsv_headers_strategy(model).index(k)
            except ValueError as e:
                raise ValueError(
                    f"Unable to update due to unexpected column {k}",
                ) from e
            yield model.index(row, column_number), updated_value

    @classmethod
    def _get_all_headers(cls, model: TsvModel) -> List[str]:
        return cls.get_tsv_headers_strategy(model)

    def get_affected_columns(self):
        """Get the affected columns."""
        return self._get_all_headers(self.model)

    def process_data(self) -> None:
        """Clean up model data."""
        model = cast(TsvModel, self.model)
        total_rows = model.rowCount()
        rows_affected: Dict[int, List[str]] = defaultdict(list)
        modifier = self.get_row_modifier_strategy(**self.settings)
        # modifier = self.get_row_modifier_strategy()
        headings = self.get_affected_columns()
        for row, row_data in self.iter_row(model):
            for index, updated_value in self.iter_new_row_data(
                model,
                row,
                row_data,
                modifier=modifier,
                # modifier=self.get_row_modifier_strategy(),
            ):
                model.setData(index, str(updated_value))
                heading = headings[index.column()]
                self.log_action(
                    f"Changed data in {index.row()}:{heading}",
                    level=logging.DEBUG,
                )

                if source := model.data(index, role=TsvModel.SourceRole):
                    rows_affected[source.line_number].append(heading)
            if len(rows_affected.get(row, [])) > 0:
                self.log_action(
                    f"{row} updating {len(rows_affected[row])} items",
                    level=logging.INFO,
                )
            self.progressChanged.emit(row / total_rows)
        total_number_of_changes: int = 0
        for row_affected in rows_affected.values():
            total_number_of_changes += len(row_affected)
        self.log_action(
            f"{total_number_of_changes} changes made", level=logging.INFO
        )

        self.submit_report(self._create_report(rows_affected))

    @classmethod
    def _create_report(cls, rows_affected) -> str:
        return cls.report_strategy(rows_affected)


@QmlElement
class JSProcessAction(ProcessingAction):
    """Javascript processing action."""

    scriptChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._action = QJSValue()

    def _set_action(self, action_: QJSValue) -> None:
        self._action = action_
        self.scriptChanged.emit()

    def _get_action(self) -> QJSValue:
        return self._action

    @Slot()
    def process_data(self) -> None:
        """Run javascript action."""
        self._action.call()
        if self._action.isError():
            raise ProcessingActionError(
                f"script failed to run. Reason: {self._action.toString()}"
            )

    script = QtCore.Property(
        QJSValue, _get_action, _set_action, notify=scriptChanged
    )
