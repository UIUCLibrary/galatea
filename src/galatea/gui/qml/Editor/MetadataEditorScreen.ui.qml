
/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick

Item {
    id: root
    width: 1200
    height: 600
    property alias model: metadataEditor.tableModel
    AppMenuBar {
        id: toolBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 0
        anchors.rightMargin: 0
        anchors.topMargin: 0
    }

    MetadataEditor {
        anchors.bottom: parent.bottom
        anchors.top: toolBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        id: metadataEditor
    }
}
