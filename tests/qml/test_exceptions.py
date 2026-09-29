import pytest

qml_exceptions = pytest.importorskip("galatea.gui.qml.exceptions")
QtQml = pytest.importorskip("PySide6.QtQml")


class TestQMLLoadingError:
    def test_str_contains_filename(self):
        assert "somefile.qml" in str(
            qml_exceptions.QMLLoadingError("somefile.qml")
        )

    def test_errors_are_included_in_str(self):
        error = QtQml.QQmlError()
        error.setUrl("somefile.qml")
        error.setLine(10)
        error.setColumn(20)
        exception = qml_exceptions.QMLLoadingError(
            "somefile.qml", errors=[error]
        )
        assert "10:20" in str(exception)
