from unittest.mock import Mock

import pytest

QtGui = pytest.importorskip("PySide6.QtGui")
QtQml = pytest.importorskip("PySide6.QtQml")
qml_app = pytest.importorskip("galatea.gui.qml.app")
qml_exceptions = pytest.importorskip("galatea.gui.qml.exceptions")


def test_qml_app():
    assert qml_app.get_icon() is not None


def test_configure_root_window_with_window_title(qtbot):
    component = Mock(spec_set=QtQml.QQmlComponent)
    qml_app.configure_root_window_with_window_title(
        component, Mock(name="Test Model"), "Test Title"
    )
    component.createWithInitialProperties.assert_called_once()


def test_create_component(tmp_path, qtbot):
    qml_file = tmp_path.joinpath("some_file.qml")
    qml_file.write_text(
        """
import QtQuick
Item{
}
""".lstrip()
    )
    engine = QtQml.QQmlApplicationEngine()
    component = qml_app.create_component(str(qml_file), engine)
    assert component is not None


def test_create_component_error(tmp_path, qtbot):
    qml_file = tmp_path.joinpath("some_file.qml")
    qml_file.write_text(
        """
Item{
}
""".lstrip()
    )
    engine = QtQml.QQmlApplicationEngine()
    with pytest.raises(qml_exceptions.QMLLoadingError):
        qml_app.create_component(str(qml_file), engine)


def test_set_app_icon():
    app = Mock()
    icon = Mock()
    qml_app.set_app_icon(app, icon)
    app.setWindowIcon.assert_called_once()


@pytest.mark.parametrize("platform", ["linux", "win32", "darwin"])
def test_get_qt_style(platform):
    assert qml_app.get_qt_style(platform) is not None


class TestTableAppBuilder:
    def test_build_uses_strategies(self, qtbot, monkeypatch):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(
            app,
            engine=QtQml.QQmlApplicationEngine(),
            backend=Mock(),
            entry_point="some_entry_point",
            icon="SomeIcon.ico",
            model=Mock(),
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "create_component_strategy", Mock()
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "set_app_icon_strategy", Mock()
        )
        builder.build()
        qml_app.TableAppBuilder.create_component_strategy.assert_called_once()

    def test_setup_engine_raises_when_engine_not_initialized(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app)
        with pytest.raises(RuntimeError):
            builder.set_up_engine()

    def test_setup_engine_raises_when_backend_not_initialized(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app)
        builder.engine = Mock()
        with pytest.raises(RuntimeError):
            builder.set_up_engine()

    def test_set_app_icon_without_icon_raises(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app)
        with pytest.raises(RuntimeError):
            builder.set_app_icon(app)

    def test_create_component_without_engine_raises(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app)
        with pytest.raises(RuntimeError):
            builder.create_component("some_entry_point")

    def test_configure_root_object_without_model_raises(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app)
        component = Mock()
        with pytest.raises(RuntimeError):
            builder.configure_root_object(component)

    def test_build_without_entry_point_raises(self, qtbot):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(app, engine=Mock(), backend=Mock())
        with pytest.raises(ValueError):
            builder.build()

    def test_configure_root_object_fails_during_build_throw_exception(
        self, monkeypatch
    ):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(
            app,
            engine=Mock(),
            backend=Mock(),
            entry_point="some_entry_point",
            model=Mock(),
            icon=Mock(),
        )

        monkeypatch.setattr(
            qml_app.TableAppBuilder, "create_component_strategy", Mock()
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "set_app_icon_strategy", Mock()
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder,
            "configure_root_object_strategy",
            Mock(return_value=None),
        )
        with pytest.raises(qml_exceptions.QMLLoadingError):
            builder.build()

    def test_build_uses_post_tasks(self, qtbot, monkeypatch):
        app = Mock(spec_set=QtGui.QGuiApplication)
        builder = qml_app.TableAppBuilder(
            app,
            engine=Mock(),
            backend=Mock(),
            entry_point="some_entry_point",
            model=Mock(),
            icon=Mock(),
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "create_component_strategy", Mock()
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "set_app_icon_strategy", Mock()
        )
        monkeypatch.setattr(
            qml_app.TableAppBuilder, "configure_root_object_strategy", Mock()
        )
        post_task = Mock()
        builder.add_post_creation_task(post_task)
        builder.build()
        post_task.assert_called_once()
