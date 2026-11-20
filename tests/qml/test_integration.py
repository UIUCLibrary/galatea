import csv
import importlib.resources

from galatea.gui.qml import backend, process_actions

import pytest
from PySide6 import QtCore, QtQml

QML_IMPORT_NAME = "Galatea"
QML_IMPORT_MAJOR_VERSION = 0


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

        processConfigure = window.findChild(QtCore.QObject, "processConfigure")
        assert processConfigure

        with qtbot.wait_signal(processConfigure.visibleChanged):
            clean_button = QtQml.QQmlProperty.read(toolbar, "cleanButton")
            assert clean_button
            clean_button.click()
        button_box = processConfigure.findChild(QtCore.QObject, "buttonBox")
        assert button_box
        with qtbot.wait_signal(modelProcessor.finished):
            button_box.accepted.emit()

        main_screen.saveFileAs.emit(QtCore.QUrl.fromLocalFile(str(out_file)))
        assert out_file.exists()
        with open(str(out_file), mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, dialect="excel-tab")
            rows = list(reader)
        assert rows[0]["Genre"] == "Maps||Fire insurance maps"
