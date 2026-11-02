import QtQuick
import QtQuick.Controls
import galatea 1.0 as GalateaBackend

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
    GalateaBackend.TsvInspector{
        id: inspector
        file: mainScreen.fileName
        onDataChanged:{
            mainScreen.state = inspector.dataIsDifferent(mainScreen.model) ? 'modified': 'unmodified'
        }
    }
    Item{
        id: stateItem
        states: [
            State{
                name: "ready"
                PropertyChanges{
                    target: mainScreen
                    enabled: true
                }
            },
            State{
                name: "loading"
                PropertyChanges{
                    target: mainScreen
                    enabled: false
                }
            }
        ]
    }
    function log(message) {
        statusBar.text = message
    }
    MetadataEditorScreen {
        objectName: "mainScreen"
        id: mainScreen
        anchors.fill: parent
        model:  SampleModel{}
        inspector: inspector
        onOpenFile: fileName => openTheFile(fileName, mainScreen.dialect ? mainScreen.dialect : Script.determineDialect(fileName), mainScreen.model)
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

