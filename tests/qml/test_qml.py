import subprocess
import sys
import os
import pytest
import importlib.resources

backend = pytest.importorskip("galatea.gui.qml.backend")

qml = pytest.importorskip("galatea.gui.qml")
QtCore = pytest.importorskip("PySide6.QtCore")
QtQml = pytest.importorskip("PySide6.QtQml")
QtQuickTest = pytest.importorskip("PySide6.QtQuickTest")


def get_test_functions(qml_file):
    results = subprocess.run(
        [
            sys.executable,
            os.path.join(
                os.path.dirname(__file__),
                "get_qml_functions.py",
            ),
            qml_file,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.removesuffix("()") for line in results.stderr.splitlines()]


def qml_test_gen(qml_file):
    qml_file_path = os.path.join(os.path.dirname(__file__), qml_file)

    def decorator(func):
        return pytest.mark.parametrize(
            "test_file, test_name",
            [
                (qml_file_path, test_name)
                for test_name in get_test_functions(qml_file_path)
            ],
        )(func)

    return decorator


class MyTestSetup(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        # This magic slot name is called automatically by the test framework

    @QtCore.Slot(QtQml.QQmlEngine)
    def qmlEngineAvailable(self, qmlEngine):
        # Instantiate your backend
        self.backend = backend.Backend()

        # Inject it into the root context so all QML tests can see it
        qmlEngine.rootContext().setContextProperty("backend", self.backend)


@pytest.fixture
def qml_tester(monkeypatch):
    def run_quick_test(qml_file, test_name=None):
        # with importlib.resources.path(galatea.gui, "qml") as qml_path:
        args = [
            __file__,
            "-v2",
            "-import",
            str(importlib.resources.files("galatea.gui.qml")),
            "-input",
            os.path.abspath(qml_file),
        ]
        if test_name:
            args.append(test_name)

        return (
            QtQuickTest.QUICK_TEST_MAIN_WITH_SETUP(
                str(qml_file), MyTestSetup, argv=args
            )
            == 0
        )
        # return QUICK_TEST_MAIN(str(qml_file), argv=args) == 0

    monkeypatch.setenv("QTEST_FUNCTION_TIMEOUT", "60")
    return run_quick_test


@qml_test_gen("tst_App.qml")
def test_App(test_file, test_name, qml_tester):
    assert qml_tester(test_file, test_name=test_name)


@qml_test_gen("tst_MetadataEditorScreen.qml")
def test_MetadataEditorScreen(qml_tester, test_file, test_name):
    assert qml_tester(test_file, test_name=test_name)
