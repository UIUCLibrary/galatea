from unittest.mock import Mock

import pytest

error_handling = pytest.importorskip("galatea.gui.qml.error_handling")
QtQml = pytest.importorskip("PySide6.QtQml")
QtGui = pytest.importorskip("PySide6.QtGui")
QtCore = pytest.importorskip("PySide6.QtCore")


class TestQMLLoadingError:
    def test_str_contains_filename(self):
        assert "somefile.qml" in str(
            error_handling.QMLLoadingError("somefile.qml")
        )

    def test_errors_are_included_in_str(self):
        error = QtQml.QQmlError()
        error.setUrl("somefile.qml")
        error.setLine(10)
        error.setColumn(20)
        exception = error_handling.QMLLoadingError(
            "somefile.qml", errors=[error]
        )
        assert "10:20" in str(exception)


def test_exit_with_fatal_error_calls_strategy():
    app = Mock()
    terminate_with_failure_strategy = Mock()
    error_handling.exit_with_fatal_error(
        app=app,
        error_window_builder=Mock(),
        terminate_with_failure_strategy=terminate_with_failure_strategy,
    )
    terminate_with_failure_strategy.assert_called_once()


def test_exit_with_fatal_error_calls_strategy_even_when_fails_to_load():
    app = Mock()
    terminate_with_failure_strategy = Mock()
    error_handling.exit_with_fatal_error(
        app=app,
        error_window_builder=Mock(
            side_effect=error_handling.QMLLoadingError(
                "", errors=["failed to load"]
            )
        ),
        terminate_with_failure_strategy=terminate_with_failure_strategy,
    )
    terminate_with_failure_strategy.assert_called_once()


def test_build_fatal_qml_error_dialog(qtbot):
    view = error_handling.build_fatal_qml_error_dialog(
        "this is an error", Mock()
    )
    details_text_area = view.contentItem().findChild(QtCore.QObject, "details")
    assert details_text_area.property("text") == "this is an error"
