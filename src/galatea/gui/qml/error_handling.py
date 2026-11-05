"""QML Gui related exception."""

import sys
from typing import Optional, List
from PySide6 import QtQml, QtQuick, QtCore, QtGui
from galatea.utils import GalateaException

__all__ = ["QMLLoadingError"]

FATAL_ERROR_QML = """
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Rectangle{
    implicitWidth: 600
    height: 400
    color: palette.window
    anchors.fill: parent
    property alias detailsText: details.text

    ColumnLayout{
        anchors.margins: 10
        anchors.fill: parent
        Layout.fillHeight: true
        spacing: 20
        Rectangle {
            Layout.fillHeight: false
            Layout.fillWidth: true
            color: palette.window
            Text{
                text: "Fatal Error"
                color: palette.windowText
            }
        }
        TextArea {
            Layout.fillHeight: true
            Layout.fillWidth: true
            padding: 5
            objectName: "details"
            id: details
            placeholderText: "No details"
            readOnly: true
            color: palette.text
        }
        DialogButtonBox{
            Layout.fillHeight: false
            Layout.fillWidth: true
            standardButtons: DialogButtonBox.Ok
            onAccepted: Qt.quit()
        }
    }
}
"""


def build_fatal_qml_error_dialog(
    details: str, app_quit_func
) -> QtQuick.QQuickView:
    view = QtQuick.QQuickView()
    view.setResizeMode(QtQuick.QQuickView.ResizeMode.SizeRootObjectToView)
    view.engine().quit.connect(app_quit_func)
    component = QtQml.QQmlComponent(view.engine())
    component.setData(
        FATAL_ERROR_QML.encode("utf-8"), QtCore.QUrl("inline.qml")
    )
    if component.isError():
        raise QMLLoadingError(__name__, errors=component.errors())
    root_object = component.createWithInitialProperties({
        "detailsText": details
    })
    view.setContent(QtCore.QUrl("inline.qml"), component, root_object)
    return view


def exit_with_fatal_error(
    app: QtGui.QGuiApplication,
    details: str = "",
    error_window_builder=build_fatal_qml_error_dialog,
    terminate_with_failure_strategy=lambda: sys.exit(-1),
):
    """Exit the application with a fatal error message."""
    try:
        error_window = error_window_builder(details, app.quit)
        error_window.show()
        app.exec()
    except QMLLoadingError as e:
        print(e.errors, file=sys.stderr)
    terminate_with_failure_strategy()


class QMLException(GalateaException):
    """QML based exception."""


class QMLLoadingError(QMLException):
    """Exception raised when there is an error loading QML files."""

    def __init__(  # noqa: D107
        self,
        file: str,
        errors: Optional[List[QtQml.QQmlError]] = None,
        *args: object,
    ) -> None:
        super().__init__(*args)
        self.file = file
        self.errors = errors or []

    def __str__(self) -> str:  # noqa: D105
        errors = []
        for error in self.errors:
            errors.append(
                f"QML Component error: "
                f"{error.url().toString()}:{error.line()}:{error.column()}: "
                f"{error.description()}"
            )
        details = "\n".join(errors)
        return f"Error loading QML file {self.file}: {details}"
