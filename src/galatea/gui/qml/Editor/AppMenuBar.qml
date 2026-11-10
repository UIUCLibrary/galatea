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
    RowLayout {
        id: rowLayout
        anchors.fill: parent

        ToolButton {
            id: toolButton
            text: qsTr("Open")
            icon.name: "document-open"

            Connections {
                target: toolButton
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
