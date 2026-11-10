import QtQuick
import QtQuick.Controls
import Galatea 1.0

import "App.js" as Script

ApplicationWindow {
    id: root
    minimumWidth: 400
    minimumHeight: 200
    height: 480
    width: 640
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
                enabled: mainScreen.state === 'modified'
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
    TsvInspector{
        id: inspector
        file: mainScreen.fileName
    }
    Item{
        id: stateItem
        states: [
            State{
                name: "ready"
                PropertyChanges{
                    mainScreen{
                        enabled: true
                    }
                }
            },
            State{
                name: "loading"
                PropertyChanges{
                    mainScreen{
                        enabled: false
                    }
                }
            }
        ]
    }
    function log(message) {
        statusBar.text = message
    }
    Dialog{
        id: notification
        title: "Job Finished"
        modal: true
        closePolicy: Popup.CloseOnEscape
        implicitWidth: 300
        implicitHeight: 200
        anchors.centerIn: parent
        contentItem: Rectangle {
            color: palette.base
            Text{
                id: informativeText
                anchors.centerIn: parent
                text: "All done"
                color: palette.text
            }
        }
        standardButtons: Dialog.Ok
    }
    MetadataEditorScreen {
        objectName: "mainScreen"
        id: mainScreen
        anchors.fill: parent
        model:  TsvModel{
            inspector: inspector
        }
        onOpenFile: fileName => openTheFile(fileName, mainScreen.dialect ? mainScreen.dialect : Script.determineDialect(fileName), mainScreen.model)
        onProcessData: (request, model) => {
            informativeText.text = "ok I'm done"
            notification.open()

        }
        function openTheFile(fileName, dialect, model){
            try{
                stateItem.state = 'loading'
                mainScreen.dialect = dialect
                if(Script.onOpenFile(fileName, mainScreen.dialect, model)) {
                    root.windowTitle = "Metadata Editor: "+ fileName
                    mainScreen.fileName = fileName
                }
                inspector.reloadFile()
            } finally {
                stateItem.state = 'ready'
            }
            mainScreen.state = inspector.dataIsDifferent(mainScreen.model) ? 'modified': 'unmodified'
        }
        onSaveFileAs: fileName => Script.onSaveFileAs(
            mainScreen.model,
            fileName,
            mainScreen.dialect,
            ()=>{
                console.log("File saved " + fileName)
                openTheFile(fileName, mainScreen.dialect, mainScreen.model)
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
    Connections {
        target: mainScreen.model
        function onDataChanged(topLeft, bottomRight, roles) {
            if(mainScreen.state !== "loading"){
                mainScreen.state = inspector.dataIsDifferent(mainScreen.model) ? 'modified': 'unmodified'
            }
        }
    }
    footer: StatusBar{
        id: statusBar
        // loading: stateItem === "loading"
    }
}

