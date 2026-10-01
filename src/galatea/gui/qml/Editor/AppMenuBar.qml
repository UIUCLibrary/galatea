import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


ToolBar {
    id: toolBar
    signal fileOpenRequested
    signal fileSaveRequested
    property alias saveButton: saveButton
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

        // ToolButton {
        //     id: importButton
        //     text: qsTr("Import")
        //     enabled: true
        //     Connections {
        //         target: importButton
        //         function onClicked() { AppMenuBarJS.onImport() }
        //     }
        // }
        // ToolSeparator {}
        // ToolButton {
        //     text: qsTr("Merge Data")
        //     onClicked: mergeMenu.open()
        //     Menu{
        //         id: mergeMenu
        //         MenuItem { text: "From GetMarc"; onTriggered: AppMenuBarJS.onMergeDataTriggered() }
        //     }
        // }
        // ToolButton {
        //     text: qsTr("Process")
        //     onClicked: processMenu.open()
        //     Menu{
        //         id: processMenu
        //         MenuItem { text: qsTr("Clean"); onTriggered: AppMenuBarJS.onCleanTriggered() }
        //         MenuItem { text: qsTr("Check Authorized Terms"); onTriggered: AppMenuBarJS.onCheckAuthorizedTerms()}
        //     }
        // }
        Item {
            Layout.fillWidth: true
        }
        ToolSeparator {}
    }
    }
