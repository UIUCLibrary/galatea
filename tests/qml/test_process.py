from unittest.mock import Mock

from PySide6 import QtCore

import pytest

from galatea.gui.qml import process_actions, process, models


class ActionTester(process_actions.ProcessingAction):
    def __init__(self, successful, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._successful = successful

    def process_data(self) -> None:
        if not self._successful:
            raise RuntimeError("Action was not successful")


class TestBackgroundWorker:
    def test_successful(self):
        dummy = ActionTester(successful=True)
        worker = process.BackgroundWorker(dummy, parent=None)
        success_callback = Mock()
        worker.add_success_callback(success_callback)
        worker.run()
        success_callback.assert_called_once()

    def test_failure(self):
        dummy = ActionTester(successful=False)
        worker = process.BackgroundWorker(dummy, parent=None)
        failure_callback = Mock()
        worker.add_failure_callback(failure_callback)
        worker.run()
        failure_callback.assert_called_once()


class TestTableModelProcessor:
    @pytest.fixture
    def processor_factory(self, qtbot):
        object_to_delete = []
        QtCore.QCoreApplication.processEvents()
        table_processor = process.TableModelProcessor()

        def _make_processor(success) -> process.TableModelProcessor:
            action = ActionTester(successful=success)
            object_to_delete.append(action)
            model = models.TsvModel()

            table_processor.model = model
            with qtbot.waitSignal(table_processor.enabledActionsChanged):
                table_processor.append_enabled_action(action)
            return action, table_processor

        yield _make_processor
        table_processor.clear_actions()
        for processor in object_to_delete:
            processor.deleteLater()
        QtCore.QCoreApplication.processEvents()

    def test_finished(self, qtbot, processor_factory):
        action, processor = processor_factory(success=True)
        with qtbot.waitSignal(processor.finished) as blocker:
            processor.processData({"action": action})
        assert blocker.signal_triggered

    @pytest.mark.parametrize(
        "expected_success, signal_affected",
        [
            (True, "success"),
            (False, "failure"),
        ],
    )
    def test_signals(
        self, qtbot, processor_factory, expected_success, signal_affected
    ):
        action, processor = processor_factory(success=expected_success)
        with qtbot.waitSignal(getattr(processor, signal_affected)) as blocker:
            processor.processData({"action": action})
        assert blocker.signal_triggered

    def test_processData_errors_are_sent_to_errorOccurred_signal(
        self, qtbot, processor_factory
    ):
        _, processor = processor_factory(success=False)
        with qtbot.waitSignal(processor.errorOccurred) as blocker:
            processor.processData({"action": "not_a_valid_job"})
        assert blocker.signal_triggered

    def test_start_action_without_model_raises_error(self, qtbot):
        table_processor = process.TableModelProcessor()
        action = ActionTester(successful=True)
        table_processor.append_enabled_action(action)
        with pytest.raises(ValueError):
            table_processor.start_action(action, {})
