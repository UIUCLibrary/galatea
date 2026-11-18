import csv
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
        # QtQml.qmlRegisterType(DummyAction, "Galatea.Backend", 1, 0, "DummyAction")
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


@QtQml.QmlElement
class DummyAction(process_actions.ProcessingAction):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.actionName = "dummy"

    def process_data(self) -> None:
        print("Dummy action")


class TestApp:
    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.root = QtCore.QObject()
        self.engine = QtQml.QQmlApplicationEngine(self.root)
        self.engine.addImportPath(
            str(importlib.resources.files("galatea.gui.qml")),
        )
        qml_file = str(
            importlib.resources.files("galatea.gui.qml").joinpath("main.qml")
        )
        self.backend = backend.Backend()
        context = self.engine.rootContext()
        context.setContextProperty("backend", self.backend)
        self.engine.load(qml_file)
        assert self.engine.hasError() is False, (
            f"Error with {qml_file}: {self.engine.catchError().toString()}"
        )
        assert len(self.engine.rootObjects()) > 0

    def test_window_change(self, qtbot):

        root = self.engine.rootObjects()[0]

        assert root.property("windowTitle") != "Something else"
        root.setProperty("windowTitle", "Something else")
        assert root.property("windowTitle") == "Something else"

    def test_process_data(self, qtbot):
        root = self.engine.rootObjects()[0]
        model_processor = QtQml.QQmlProperty.read(root, "modelProcessor")
        action = DummyAction()
        list_ref = QtQml.QQmlListReference(model_processor, "enabledActions")
        assert all([
            list_ref.isValid(),
            list_ref.canAppend(),
            list_ref.canClear(),
            list_ref.canCount(),
        ])
        list_ref.clear()
        assert list_ref.count() == 0
        assert list_ref.append(action)
        assert list_ref.count() > 0
        with qtbot.wait_signal(model_processor.finished):
            model_processor.processData({"action": action})

    def test_clean(self, qtbot, tmp_path):
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        out_file = sub_dir / "outfile.tsv"
        test_file = sub_dir / "source.tsv"
        test_file.write_text(
            """uuid	parentId	preservationMasterPathname	preservationMasterFilename	preservationMasterUUID	accessMasterPathname	accessMasterFilename	accessMasterUUID	variant	pageNumber	subpageNumber	published	contentdmAlias	contentdmPointer	IGNORE	Title	Alternative Title	Creator	Coverage-Spatial	Genre	Subject	Publisher	Date of Publication	Place of Publication	Scale	Language	Notes	Extent	Dimensions	Coordinates	rights:Rights	Rights Description	resourceType:Type	provider:Repository	Local Bib ID	Collection Title
8104f370-b18b-013c-4bcb-02d0d7bfd6e4-5											FALSE			0	Taylorville, Christian County, Illinois, May 1931	Taylorville, Ill.	Sanborn Map Company.	Illinois||Taylorville||Illinois||Taylorville||Taylorville (Ill.)	Maps.||Maps.||Maps.||Fire insurance maps.	Fire insurance||Fire risk assessment	Sanborn Map Company,	c1931.	New York :	Scale [ca. 1:600]. 50 ft. to one inch		Also shows factories, commercial occupancy of buildings, property boundaries and house and block numbers.||Fire insurance map hand colored to show building construction, locations of windows and doors, elevators, and available water facilities.||Sheet 1 includes symbol key, index, and location and index maps.||Partial cadastral map.	28 maps : col. ;	on sheets 65 x 55 cm.	(W 89⁰17ʹ40ʺ/N 39⁰32ʹ56ʺ)					99162599612205899	
355adbe0-b19c-013c-4bcb-02d0d7bfd6e4-7	8104f370-b18b-013c-4bcb-02d0d7bfd6e4-5	162/2204/99162599612205899/preservation/99162599612205899-002.tif	99162599612205899-002.tif	355adbe0-b19c-013c-4bcb-02d0d7bfd6e4-7	162/2204/99162599612205899/access/99162599612205899-002.jp2	99162599612205899-002.jp2	34fccd20-b19c-013c-4bcb-02d0d7bfd6e4-4	Page			TRUE			0	99162599612205899-002.tif																				
355adbe0-b19c-013c-4bcb-02d0d7bfd6e4-7	8104f370-b18b-013c-4bcb-02d0d7bfd6e4-5	162/2204/99162599612205899/preservation/99162599612205899-002.tif	99162599612205899-002.tif	355adbe0-b19c-013c-4bcb-02d0d7bfd6e4-7	162/2204/99162599612205899/access/99162599612205899-002.jp2	99162599612205899-002.jp2	34fccd20-b19c-013c-4bcb-02d0d7bfd6e4-4	Page			TRUE			0	99162599612205899-002.tif	Taylorville, Ill.	Sanborn Map Company.	Illinois||Taylorville||Illinois||Taylorville||Taylorville (Ill.)	Maps.||Maps.||Maps.||Fire insurance maps.	Fire insurance||Fire risk assessment	Sanborn Map Company,	c1931.	New York :	Scale [ca. 1:600]. 50 ft. to one inch		Also shows factories, commercial occupancy of buildings, property boundaries and house and block numbers.||Fire insurance map hand colored to show building construction, locations of windows and doors, elevators, and available water facilities.||Sheet 1 includes symbol key, index, and location and index maps.||Partial cadastral map.	28 maps : col. ;	on sheets 65 x 55 cm.	(W 89⁰17ʹ40ʺ/N 39⁰32ʹ56ʺ)						
            """.strip(),
            encoding="utf-8",
        )
        with open(str(test_file), mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, dialect="excel-tab")
            rows = list(reader)
        assert rows[0]["Genre"] == "Maps.||Maps.||Maps.||Fire insurance maps."

        window = self.engine.rootObjects()[0]
        main_screen = window.findChild(QtCore.QObject, "mainScreen")
        assert main_screen

        main_screen.openFile.emit(QtCore.QUrl.fromLocalFile(str(test_file)))

        toolbar = QtQml.QQmlProperty.read(main_screen, "tools")
        assert toolbar
        modelProcessor = QtQml.QQmlProperty.read(window, "modelProcessor")
        assert modelProcessor
        with qtbot.wait_signal(modelProcessor.finished):
            clean_button = QtQml.QQmlProperty.read(toolbar, "cleanButton")
            assert clean_button
            clean_button.click()
        main_screen.saveFileAs.emit(QtCore.QUrl.fromLocalFile(str(out_file)))
        assert out_file.exists()
        with open(str(out_file), mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, dialect="excel-tab")
            rows = list(reader)
        assert rows[0]["Genre"] == "Maps||Fire insurance maps"
