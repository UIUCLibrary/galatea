"""QQml based tsv Editor."""

import argparse
import functools
import importlib.resources
import logging
import sys
from importlib.metadata import version
from typing import Optional, List

from galatea.gui.qml import backend
from galatea.gui.qml import exceptions as qml_exceptions
from galatea.gui.qml import models
from galatea.gui.qml import app as qml_app
from galatea.gui.qml import log as qml_logging
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6 import QtCore, QtGui, QtQml, QtQuick

__all__ = ["main"]


module_logger = logging.getLogger("QML")
module_logger.setLevel(logging.DEBUG)


def set_app_with_starting_file(
    root_object: QtQuick.QQuickItem, tsv_file: str
) -> None:
    if item := root_object.findChild(QtQuick.QQuickItem, "mainScreen"):
        item.setProperty("fileName", tsv_file)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("tsv", type=str, nargs="?", help="tsv file path")
    return parser


def build_qml_app(
    app: QtGui.QGuiApplication,
    args: argparse.Namespace,
    engine=None,
    python_backend=None,
    application_builder=None,
    model=None,
):
    engine = engine or QtQml.QQmlApplicationEngine(parent=app)
    python_backend = python_backend or backend.Backend(app)
    display_in_qml = qml_logging.LogSignalHandler(python_backend.logSubmitted)
    module_logger.addHandler(display_in_qml)
    QtCore.qInstallMessageHandler(
        functools.partial(
            qml_logging.qt_message_handler, module_logger, include_context=True
        )
    )
    application_builder = application_builder or qml_app.TableAppBuilder(app)

    application_builder.model = model or models.TsvModel(app)
    application_builder.backend = python_backend
    application_builder.engine = engine
    application_builder.icon = qml_app.get_icon()

    entry_point = (
        importlib.resources.files("galatea.gui.qml")
        .joinpath("Editor")
        .joinpath("App.qml")
    )
    application_builder.entry_point = str(entry_point)

    if args.tsv:
        application_builder.add_post_creation_task(
            lambda root_object: set_app_with_starting_file(
                root_object, args.tsv
            )
        )
    application_builder.build()


def main(
    argv: Optional[List[str]] = None,
    app=None,
    build_app_strategy=build_qml_app,
) -> int:
    """Run the QML based editor."""
    args = get_arg_parser().parse_args(
        argv if argv is not None else sys.argv[1:]
    )
    qt_style = qml_app.get_qt_style()

    QQuickStyle.setStyle(qt_style)
    print("Compiled Qt Version:", version("pyside6"))
    app = app or QtGui.QGuiApplication()

    build_app_strategy(app, args)
    return app.exec()


if __name__ == "__main__":
    try:
        main()
    except qml_exceptions.QMLLoadingError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
