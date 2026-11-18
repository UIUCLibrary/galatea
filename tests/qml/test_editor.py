import importlib.resources
from unittest.mock import Mock

from PySide6 import QtQml, QtGui, QtQuick
from galatea.gui import editor
from galatea.gui.qml import backend
from galatea.gui.qml import app as qml_app


def test_main_calls_exec(qtbot):
    app = Mock(spec_set=QtGui.QGuiApplication)
    editor.main(app=app, argv=[], build_app_strategy=Mock())
    app.exec.assert_called_once()


def test_build_qml_app(qtbot):
    app = Mock(spec_set=QtGui.QGuiApplication)
    builder = Mock()
    editor.build_qml_app(
        app,
        args=Mock(),
        engine=Mock(),
        python_backend=Mock(),
        application_builder=builder,
    )
    builder.build.assert_called_once()


def test_set_app_with_starting_file(qtbot, monkeypatch):
    engine = QtQml.QQmlApplicationEngine()
    backend.Backend()
    engine.rootContext().setContextProperty(
        "backend",
        None,
    )
    component = qml_app.create_component(
        str(importlib.resources.files("galatea.gui.qml").joinpath("main.qml")),
        engine,
    )
    assert not component.errors()
    window = component.create()
    setProperty = Mock()
    monkeypatch.setattr(QtQuick.QQuickItem, "setProperty", setProperty)
    editor.set_app_with_starting_file(window, "test.tsv")
    setProperty.assert_called_once()


def test_get_entry_point_from_local():
    assert editor.get_entry_point_from_local()


def test_get_entry_point_from_resource():
    assert editor.get_entry_point_from_resource()


def test_locate_qml_entry_point_file():
    strategy = [Mock(return_value="main.qml")]
    assert editor.locate_qml_entry_point_file(strategy) == "main.qml"


def test_locate_qml_entry_point_file_fails_with_none():
    strategy = [Mock(return_value=None)]
    assert editor.locate_qml_entry_point_file(strategy) is None
