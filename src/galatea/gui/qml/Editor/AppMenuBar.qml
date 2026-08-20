import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "AppMenuBar.js" as AppMenuBarJS


ToolBar {
    id: toolBar
    RowLayout {
        id: rowLayout
        anchors.fill: parent

        ToolButton {
            id: toolButton
            text: qsTr("Open")
            icon.name: "document-open"

            Connections {
                target: toolButton
                function onClicked() { AppMenuBarJS.onCheckAuthorizedTerms() }
            }
        }
        
        ToolButton {
            id: saveButton
            text: qsTr("Save")
            icon.name: "document-save"
            enabled: true

            Connections {
                target: saveButton
                function onClicked() { AppMenuBarJS.onSaveFile() }
            }
        }

        ToolButton {
            id: importButton
            text: qsTr("Import")
            enabled: true
            Connections {
                target: importButton
                function onClicked() { AppMenuBarJS.onImport() }
            }
        }
        ToolSeparator {}
        ToolButton {
            text: qsTr("Merge Data")
            onClicked: mergeMenu.open()
            Menu{
                id: mergeMenu
                MenuItem { text: "From GetMarc"; onTriggered: AppMenuBarJS.onMergeDataTriggered() }
            }
        }
        ToolButton {
            text: qsTr("Process")
            onClicked: processMenu.open()
            Menu{
                id: processMenu
                MenuItem { text: qsTr("Clean"); onTriggered: AppMenuBarJS.onCleanTriggered() }
                MenuItem { text: qsTr("Check Authorized Terms"); onTriggered: AppMenuBarJS.onCheckAuthorizedTerms()}
            }
        }
        Item {
            Layout.fillWidth: true
        }
        ToolSeparator {}
    }
    }
