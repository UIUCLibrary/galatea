import glob
import subprocess
import sys
import os
import pytest
import importlib.resources
import tempfile

from galatea.gui.qml import process_actions, backend
from PySide6 import QtCore
from PySide6 import QtQml
from PySide6 import QtQuickTest


QML_IMPORT_NAME = "Galatea"
QML_IMPORT_MAJOR_VERSION = 0


def parse_qml_tests_response(qml_functions_results):
    if qml_functions_results.returncode != 0:
        if qml_functions_results.stdout.strip() != "":
            print(qml_functions_results.stdout)

        if qml_functions_results.stderr.strip() != "":
            print(qml_functions_results.stderr)

        raise subprocess.CalledProcessError(
            returncode=qml_functions_results.returncode,
            cmd="get_qml_functions.py",
            output=qml_functions_results.stdout,
            stderr=qml_functions_results.stderr,
        )
    return [
        line.removesuffix("()")
        for line in qml_functions_results.stderr.splitlines()
    ]


class GenerationError(Exception):
    pass


def get_test_functions(qml_file):
    try:
        return parse_qml_tests_response(
            subprocess.run(
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
        )
    except subprocess.CalledProcessError as e:
        raise GenerationError(
            e.stderr if e.stderr.strip() != "" else e.stdout
        ) from e


@QtQml.QmlElement
class DummyAction(process_actions.ProcessingAction):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.actionName = "dummy"

    def process_data(self) -> None:
        print("Dummy action")


class MyTestSetup(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        # This magic slot name is called automatically by the test framework

    @QtCore.Slot(QtQml.QQmlEngine)
    def qmlEngineAvailable(self, qmlEngine: QtQml.QQmlEngine):
        # Instantiate your backend
        self.backend = backend.Backend()
        context = qmlEngine.rootContext()
        # Inject it into the root context so all QML tests can see it
        context.setContextProperty("backend", self.backend)
        context.setContextProperty("DummyAction", DummyAction)

        def cleanup():
            print("destroyed")
            print("waiting for threads")
            QtCore.QThreadPool.globalInstance().waitForDone()
            print("waiting for threads -Done")

        context.destroyed.connect(cleanup)


def run_quick_test(qml_file, test_name=None):
    args = [
        __file__,
        "-v2",
        "-import",
        str(importlib.resources.files("galatea.gui.qml")),
        "-input",
        os.path.abspath(os.path.join(os.path.dirname(__file__), qml_file)),
    ]
    if test_name:
        args.append(test_name)

    return (
        QtQuickTest.QUICK_TEST_MAIN_WITH_SETUP(
            str(qml_file), MyTestSetup, argv=args
        )
        == 0
    )


skip_files_list = {
    "tst_App.qml",
    # "tst_sanity.qml",
    # "tst_TableModelProcessor.qml",
    # "tst_MetadataEditorScreen.qml"
}


def pytest_generate_tests(metafunc):
    if "qml_test" in metafunc.fixturenames:
        test_location = os.path.join(os.path.dirname(__file__))
        qml_test_files = [
            f for f in glob.glob("tst_*.qml", root_dir=test_location)
        ]
        res = []
        for qml_file in qml_test_files:
            if qml_file in skip_files_list:
                continue
            try:
                for test_name in get_test_functions(
                    os.path.join(test_location, qml_file)
                ):
                    res.append(
                        pytest.param(
                            (qml_file, test_name),
                            id=f"{qml_file}-{test_name}",
                            marks=pytest.mark.skipif(
                                qml_file in skip_files_list, reason="Skip test"
                            ),
                        )
                    )
            except GenerationError as error_message:
                res.append(
                    pytest.param(
                        (qml_file, None),
                        id=f"{qml_file}",
                        marks=pytest.mark.fail_immediately(
                            reason=f"Unable to generate tests for {qml_file}. reason: {error_message}",
                        ),
                    )
                )
        metafunc.parametrize("qml_test", res)


def test_qml_files(monkeypatch, qml_test):
    # monkeypatch.setenv("QTEST_FUNCTION_TIMEOUT", "60")
    test_file, test_name = qml_test
    script_file = os.path.join(os.path.dirname(__file__), "run_qml_tests.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        report_file_name = os.path.join(tmpdir, "report.txt")
        timeout_seconds = 10
        test_env_vars = {
            "QTEST_FUNCTION_TIMEOUT": str(timeout_seconds * 1000),
        }
        if qt_qta_platform := os.getenv("QT_QPA_PLATFORM"):
            test_env_vars["QT_QPA_PLATFORM"] = qt_qta_platform
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    script_file,
                    test_file,
                    f"--test-name={test_name}",
                    f"--report_file_name={report_file_name}",
                ],
                env=test_env_vars,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as e:
            print(e)
            if e.stderr:
                print(e.stderr.decode("utf-8"), file=sys.stderr)
            if e.stdout:
                print(e.stdout.decode("utf-8"), file=sys.stderr)
            pytest.fail("Test timeout expired")
        finally:
            if os.path.exists(report_file_name):
                with open(report_file_name, "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print(f"{report_file_name} not found.", file=sys.stderr)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        pytest.fail(
            f"Error running tests with {os.path.join(os.path.dirname(__file__), test_file)}.\n{result.stderr}"
        )
