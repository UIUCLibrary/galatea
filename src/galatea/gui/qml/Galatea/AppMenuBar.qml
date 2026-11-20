import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


ToolBar {
    id: toolBar
    signal fileOpenRequested
    signal fileSaveRequested
    signal processRequested
    signal cleanRequested
    property alias saveButton: saveButton
    property alias processButton: processButton
    property alias cleanButton: cleanButton
    property alias openButton: openButton
    RowLayout {
        id: rowLayout
        anchors.fill: parent

        ToolButton {
            id: openButton
            text: qsTr("Open")
            icon.name: "document-open"

            Connections {
                target: openButton
                function onClicked() {
                    toolBar.fileOpenRequested()
                }
            }
        }

        ToolButton {
            id: saveButton
            text: qsTr("Save")
            icon.name: "document-save"
            enabled: false

            Connections {
                target: saveButton
                function onClicked() {
                    toolBar.fileSaveRequested()
                }
            }
        }
        ToolSeparator {}
        ToolButton {
            id: processButton
            text: qsTr("Process")
            onClicked: toolBar.processRequested()
        }
        ToolButton {
            id: cleanButton
            text: qsTr("Clean")
            onClicked: toolBar.cleanRequested()
        }
        Item {
            Layout.fillWidth: true
        }
        ToolSeparator {}
    }
}
