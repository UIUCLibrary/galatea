"""Table Application."""

from __future__ import annotations

import functools
import importlib.resources
import sys
from typing import Optional, Callable, TYPE_CHECKING

from PySide6 import QtGui, QtQml, QtCore
from galatea.gui.qml import exceptions as qml_exceptions
from galatea.gui.qml import models

if TYPE_CHECKING:
    from PySide6.QtQml import QQmlApplicationEngine, QQmlEngine, QQmlComponent
    from galatea.gui.qml.backend import Backend


def get_icon() -> str:
    """Return the path to the application icon."""
    return str(importlib.resources.files("galatea").joinpath("galatea.ico"))


def configure_root_window_with_window_title(
    component: QQmlComponent, model: models.TsvModel, window_title: str
) -> Optional[QtCore.QObject]:
    """Configure the root object of the QML component with a window title."""
    return component.createWithInitialProperties({
        "windowTitle": window_title,
        "model": model,
    })


def create_component(file: str, engine: QQmlEngine):
    """Create a QML component from a file."""
    component = QtQml.QQmlComponent(engine, QtCore.QUrl.fromLocalFile(file))
    if component.isError():
        raise qml_exceptions.QMLLoadingError(
            file=str(file), errors=component.errors()
        )
    return component


def set_app_icon(app: QtGui.QGuiApplication, icon: str):
    """Set application icon."""
    app.setWindowIcon(QtGui.QIcon(str(icon)))


class TableAppBuilder:
    """Table Application configuration builder."""

    create_component_strategy = create_component
    configure_root_object_strategy = functools.partial(
        configure_root_window_with_window_title,
        window_title="Metadata Editor with Python backend",
    )
    set_app_icon_strategy = set_app_icon

    def __init__(self, app: QtGui.QGuiApplication, **kwargs) -> None:
        """Initialize the TableAppBuilder."""
        super().__init__()
        self.app = app
        self.icon: Optional[str] = kwargs.get("icon", None)
        self.backend: Optional[Backend] = kwargs.get("backend", None)
        self.engine: Optional[QQmlApplicationEngine] = kwargs.get(
            "engine", None
        )

        self.entry_point: Optional[str] = kwargs.get("entry_point", None)
        self.model: Optional[models.TsvModel] = kwargs.get("model", None)
        self.post_tasks = []

    def set_app_icon(self, app: QtGui.QGuiApplication) -> None:
        """Set the application icon."""
        if not self.icon:
            raise RuntimeError("Icon not initialized")
        TableAppBuilder.set_app_icon_strategy(app, self.icon)

    def add_post_creation_task(self, task: Callable[[QtCore.QObject], None]):
        """Add a task to be executed after the QML engine is initialized."""
        self.post_tasks.append(task)

    def set_up_engine(self):
        """Set up the QML engine with the backend."""
        if not self.engine:
            raise RuntimeError("Engine not initialized")

        self.engine.quit.connect(self.app.quit)
        if not self.backend:
            raise RuntimeError("Backend not initialized")

        self.engine.rootContext().setContextProperty(
            "backend",
            self.backend,
        )

    def create_component(self, file: str) -> QQmlComponent:
        """Create a QML component from a file."""
        if not self.engine:
            raise RuntimeError("Engine not initialized")
        return TableAppBuilder.create_component_strategy(file, self.engine)

    def configure_root_object(self, component: QQmlComponent):
        """Configure the root object of the application."""
        if not self.model:
            raise RuntimeError("Model not initialized")
        return TableAppBuilder.configure_root_object_strategy(
            component, self.model
        )

    def build(self) -> None:
        """Build the application."""
        self.set_up_engine()
        if not self.entry_point:
            raise ValueError("entry_point required to build application")
        component = self.create_component(self.entry_point)
        self.set_app_icon(self.app)
        root_object = self.configure_root_object(component)
        if not root_object:
            raise qml_exceptions.QMLLoadingError(file=str(self.entry_point))

        for task in self.post_tasks:
            task(root_object)


def get_qt_style(platform: str = sys.platform) -> str:
    """Get the Qt style based on the platform."""
    match platform:
        case "win32":
            return "Windows"
        case "darwin":
            return "macOS"
    return "Fusion"
