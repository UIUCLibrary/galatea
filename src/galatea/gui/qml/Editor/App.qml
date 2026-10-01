import QtQuick
import QtQuick.Controls

import "App.js" as Script

ApplicationWindow {
    id: root
    minimumWidth: 400
    minimumHeight: 200
    property string windowTitle: "Metadata Editor"
    property alias model: mainScreen.model
    visible: true
    title: windowTitle
    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            Action { text: qsTr("&New...") }
            MenuSeparator { }
            Action {
                text: qsTr("&Open...")
                shortcut: StandardKey.Open
                icon.name: "document-open"
                onTriggered: mainScreen.openFileRequested()
            }
            MenuSeparator { }
            Action {
                id: saveAction
                text: qsTr("&Save")
                shortcut: StandardKey.Save
                icon.name: "document-save"
                enabled: mainScreen.model.isModified
                onTriggered: mainScreen.handleSaveRequest()
            }
            Action {
                text: qsTr("Save &As...")
                enabled: !mainScreen.model.isEmpty
                onTriggered: mainScreen.saveAs()
            }
            MenuSeparator { }
            Action {
                text: qsTr("&Quit")
                shortcut: StandardKey.Quit
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("Merge Data")
            visible: false
            // Action {text: qsTr("From GetMarc")}
        }
        Menu {
            title: qsTr("Process")
            visible: false
            // Action { text: qsTr("Clean") }
            // Action { text: qsTr("Check Authorized Terms") }
        }
    }
    function log(message) {
        statusBar.text = message
    }
    MetadataEditorScreen {
        objectName: "mainScreen"
        id: mainScreen
        anchors.fill: parent
        model:  SampleModel{}
        onOpenFile: fileName => {
            mainScreen.dialect = Script.determineDialect(fileName)
            if(Script.onOpenFile(fileName, mainScreen.dialect, mainScreen.model)) {
                root.windowTitle = "Metadata Editor: "+ fileName
            }
        }
        onSaveFileAs: fileName => Script.onSaveFileAs(
            mainScreen.model,
            fileName,
            mainScreen.dialect,
            ()=>{
                console.log("File saved " + fileName)
                Script.onOpenFile(fileName, mainScreen.dialect, mainScreen.model)
            },
            ()=>{
                console.error("Failed to save")
            }

        )
    }
    Connections {
        target: backend
        function onLogSubmitted(message) {
            root.log(message)
        }
    }
    footer: StatusBar{
        id: statusBar
    }
}

