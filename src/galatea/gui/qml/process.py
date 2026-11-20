"""Process data."""

import abc
import sys
from typing import (
    Any,
    Dict,
    Callable,
    List,
    Set,
)

from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QmlElement
from PySide6 import QtQml
import shiboken6
from galatea.gui.qml.models import TsvModel
from galatea.gui.qml import process_actions

QML_IMPORT_NAME = "Galatea"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

__all__ = ["TableModelProcessor"]


@QmlElement
class TableModelProcessor(QObject):
    """Table model processor."""

    enabledActionsChanged = QtCore.Signal()
    modelChanged = QtCore.Signal()
    errorOccurred = QtCore.Signal(str)
    stateChanged = QtCore.Signal(str)
    reportCreated = QtCore.Signal(str)
    progressChanged = QtCore.Signal(float)
    actionLogged = QtCore.Signal(str, int)
    finished = QtCore.Signal()
    success = QtCore.Signal()
    failure = QtCore.Signal(str)

    def __init__(self, *args, **kwargs) -> None:
        """Initialize processor."""
        super().__init__(*args, **kwargs)
        self._actions: Set[process_actions.ProcessingAction] = set()
        self._states: Dict[str, AbsTableModelProcessorState] = {
            "idle": IdleProcessingState(self),
            "processing": ProcessingState(self),
        }
        self._report = ""
        self._state: AbsTableModelProcessorState = self._states["idle"]

        self.destroyed.connect(self._state.clear_callbacks)

        def on_finished():
            if shiboken6.isValid(self) and shiboken6.isValid(self.finished):
                self.finished.emit()

        def on_succeeded():
            if shiboken6.isValid(self) and shiboken6.isValid(self.success):
                self.success.emit()

        self._state.connect_on_finished(on_finished)
        self._state.connect_on_success(on_succeeded)
        self._state.connect_on_failure(self.failure.emit)
        self._model: TsvModel | None = None

        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self.thread_pool.setParent(self)
        self.thread_pool.setMaxThreadCount(2)

    @Slot()
    def waitForDone(self) -> None:
        """Wait for the process to finish."""
        print("waiting for done", file=sys.stderr)
        self.thread_pool.waitForDone()

    def set_state(self, name: str) -> None:
        """Set the state of the processor."""
        self._state = self._states[name]
        # if self._is_active:
        if shiboken6.isValid(self):
            self.stateChanged.emit(name)
        print(f"state changed to {name}")

    @Slot(dict)
    def processData(self, data: Dict[str, Any]) -> None:
        """Process data."""
        try:
            action: process_actions.ProcessingAction | None = data.pop(
                "action", None
            )
            if action is None:
                raise ValueError("missing 'action' parameter")
            if action not in self._actions:
                raise ValueError(f"Unregistered action: {action}")
            action.setParent(self)
            self.start_action(action, data)

        except ValueError as e:
            self.errorOccurred.emit(str(e))

    def start_action(
        self, action: process_actions.ProcessingAction, data: Dict[str, Any]
    ) -> None:
        """Start the action."""
        if self._model is None:
            raise ValueError("model not set")
        action.set_model(self._model)
        action.progressChanged.connect(self.progressChanged)
        action.actionLogged.connect(self.actionLogged)
        action.reportGenerated.connect(self.set_report)

        def on_destroyed(action_):
            action_.success.disconnect(self.success)

        action.destroyed.connect(lambda action_=action: on_destroyed)
        action.setParent(self)
        self._state.process_data(action, data)

    def _get_model(self) -> TsvModel | None:
        return self._model

    def _set_model(self, model: TsvModel) -> None:
        self._model = model

    def append_enabled_action(
        self, value: process_actions.ProcessingAction
    ) -> None:
        """Append an enabled action."""
        self._actions.add(value)
        self.enabledActionsChanged.emit()

    def _count_actions(self) -> int:
        return len(self._actions)

    def clear_actions(self) -> None:
        """Clear all enabled actions."""
        self._actions.clear()

    def _get_actions(self):
        actions = {}
        for action in self._actions:
            actions[action.actionName] = action
        return actions

    def _get_state_name(self):
        return self._state.state_name()

    def _get_report(self):
        return self._report

    def set_report(self, value: str):
        """Set the report data."""
        self._report = value
        self.reportCreated.emit(value)

    model = QtCore.Property(
        TsvModel, _get_model, _set_model, notify=modelChanged
    )
    state = QtCore.Property(str, _get_state_name, notify=stateChanged)

    enabledActions = QtQml.ListProperty(
        process_actions.ProcessingAction,
        append_enabled_action,
        count=_count_actions,
        clear=clear_actions,
    )
    actions = QtCore.Property(dict, _get_actions, notify=enabledActionsChanged)
    report = QtCore.Property(str, _get_report, notify=reportCreated)


class BackgroundWorker(QtCore.QRunnable):
    def __init__(self, action: process_actions.ProcessingAction, **kwargs):
        super().__init__()
        self._kwargs = kwargs
        self.action = action
        self._on_failure_callbacks: List[Callable[[str], None]] = []
        self._on_finished_callbacks: List[Callable[[], None]] = []
        self._on_success_callbacks: List[Callable[[], None]] = []

    def add_finished_callback(self, callback: Callable[[], None]) -> None:
        self._on_finished_callbacks.append(callback)

    def _notify_finished(self):
        for callback in self._on_finished_callbacks:
            callback()

    def add_success_callback(self, callback: Callable[[], None]) -> None:
        self._on_success_callbacks.append(callback)

    def _notify_success(self):
        for callback in self._on_success_callbacks:
            callback()

    def add_failure_callback(self, callback: Callable[[str], None]) -> None:
        self._on_failure_callbacks.append(callback)

    def _notify_failure(self, message: str) -> None:
        for callback in self._on_failure_callbacks:
            callback(message)

    @Slot()
    def run(self) -> None:
        """Run the background worker and notify success and failure."""
        try:
            self.action.settings = self._kwargs.get("data", {})
            self.action.run()
            self._notify_success()
        except Exception as e:
            self._notify_failure(str(e))
        finally:
            self._notify_finished()


class AbsTableModelProcessorState(abc.ABC):
    failure_callbacks: List[Callable[[str], None]] = []
    finished_callbacks: List[Callable[[], None]] = []
    success_callbacks: List[Callable[[], None]] = []

    parent_was_deleted = False

    @classmethod
    def connect_on_failure(cls, callback: Callable[[str], None]) -> None:
        cls.failure_callbacks.append(callback)

    @classmethod
    def notify_failure(cls, message: str) -> None:
        for callback in cls.failure_callbacks:
            callback(message)

    @classmethod
    def connect_on_success(cls, callback: Callable[[], None]) -> None:
        cls.success_callbacks.append(callback)

    @classmethod
    def clear_callbacks(cls):
        cls.finished_callbacks.clear()
        cls.success_callbacks.clear()
        cls.failure_callbacks.clear()

    @classmethod
    def notify_success(cls):
        for callback in cls.success_callbacks:
            callback()

    @classmethod
    def connect_on_finished(cls, callback: Callable[[], None]) -> None:
        cls.finished_callbacks.append(callback)

    @classmethod
    def notify_finished(cls):
        for callback in cls.finished_callbacks:
            callback()

    def __init__(self, parent: TableModelProcessor) -> None:
        super().__init__()
        self.parent = parent

    @abc.abstractmethod
    def state_name(self) -> str:
        pass

    @abc.abstractmethod
    def process_data(
        self, action: process_actions.ProcessingAction, data: Dict[str, Any]
    ) -> None:
        pass


class IdleProcessingState(AbsTableModelProcessorState):
    def __init__(self, parent: TableModelProcessor) -> None:
        super().__init__(parent)
        self._active = True

    def state_name(self) -> str:
        return "idle"

    def process_data(
        self, action: process_actions.ProcessingAction, data: Dict[str, Any]
    ) -> None:
        worker = BackgroundWorker(
            action,
            data=data,
        )
        self.parent.set_report("")
        self.parent.set_state("processing")
        worker.add_finished_callback(lambda: self.parent.set_state("idle"))

        def get_report():
            if report := self.parent.report:
                self.parent.set_report(report)

        worker.add_finished_callback(get_report)
        worker.add_finished_callback(self.notify_finished)
        worker.add_success_callback(self.notify_success)
        worker.add_failure_callback(self.notify_failure)
        self.parent.thread_pool.start(worker, priority=5)
        QtCore.QCoreApplication.processEvents()


class ProcessingState(AbsTableModelProcessorState):
    def state_name(self) -> str:
        return "processing"

    def process_data(
        self, action: process_actions.ProcessingAction, data: Dict[str, Any]
    ) -> None:
        print("Already running")
