import pytest
from galatea import clean_tsv, modifiers
from galatea.tsv import TableRow

from galatea.gui.qml import error_handling
from galatea.gui.qml import models
from galatea.gui.qml import process_actions
from PySide6 import QtQml


class TestJSProcessAction:
    def test_success(self, qtbot):
        process = process_actions.JSProcessAction()
        engine = QtQml.QJSEngine()
        process.script = engine.evaluate("let foo = 1 + 2")

        process.process_data()

    def test_error(self, qtbot):
        process = process_actions.JSProcessAction()
        engine = QtQml.QJSEngine()
        process.script = engine.evaluate(
            'throw new Error("Cannot divide by zero.")'
        )
        with pytest.raises(error_handling.ProcessingActionError):
            process.process_data()

    def test_notify_callback_changed(self, qtbot):
        process = process_actions.JSProcessAction()
        engine = QtQml.QJSEngine()
        action = engine.evaluate("1 + 2")
        with qtbot.waitSignal(process.scriptChanged) as blocker:
            process.script = action
        assert blocker.signal_triggered
        assert process.script == action


class TestCleanAction:
    def test_success(self, qtbot, model):
        process = process_actions.CleanAction()
        # process.process_data = Mock()
        process.model = model
        with qtbot.waitSignal(model.dataChanged) as blocker:
            process.run()
        assert blocker.signal_triggered

    @pytest.fixture
    def model(self):
        model = models.TsvModel()
        models.load_tsv_model(
            model,
            ["first", "second"],
            [
                TableRow(1, {"first": "1a.", "second": "1b"}),
                TableRow(2, {"first": "2a.", "second": "2b"}),
            ],
        )
        return model

    def test_iter_row(self, model):
        assert len(list(process_actions.CleanAction.iter_row(model))) == 2

    def test_iter_new_row_data(self, model):
        modifier = clean_tsv.RowTransformer()
        modifier.add_transformation(
            lambda entry: modifiers.split_and_modify(
                entry, funcs=[modifiers.remove_trailing_punctuation]
            )
        )
        results = list(
            process_actions.CleanAction.iter_new_row_data(
                model,
                1,
                {"first": "1a.", "second": "1b"},
                modifier=modifier,
            )
        )
        assert len(results) == 1

    def test_iter_new_row_data_invalid_headings_raise(self, model):
        modifier = clean_tsv.RowTransformer()
        modifier.add_transformation(
            lambda entry: modifiers.split_and_modify(
                entry, funcs=[modifiers.remove_trailing_punctuation]
            )
        )
        with pytest.raises(ValueError):
            # There is no "third" in the row data
            list(
                process_actions.CleanAction.iter_new_row_data(
                    model,
                    1,
                    {"first": "1a.", "third": "1b."},
                    modifier=modifier,
                )
            )

    def test_process_data_submits_report(self, model, qtbot):
        process = process_actions.CleanAction()
        process.model = model
        with qtbot.waitSignal(process.reportGenerated) as blocker:
            process.process_data()
        assert blocker.signal_triggered
        assert process.get_report() != ""

    def test_get_action_name(self):
        process = process_actions.CleanAction()
        assert process.get_action_name() == "clean"
