import QtQuick
import QtQuick.Controls

import Galatea
import "app.js" as Script

ApplicationWindow {
    id: root
    minimumWidth: 400
    minimumHeight: 200
    height: 480
    width: 640
    property string windowTitle: "Metadata Editor"
    property alias model: mainScreen.model
    property alias mainScreen: mainScreen
    readonly property alias modelProcessor: modelProcessor
    readonly property alias notification: notification
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
                id: saveAsAction
                objectName: "saveAsAction"
                text: qsTr("Save &As...")
                enabled: mainScreen.model ? !mainScreen.model.isEmpty : false
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
                    statusBar{
                        loading: true
                    }
                }
            },
            State{
                name: "processing"
                when: modelProcessor && modelProcessor.state === "processing"
                PropertyChanges{
                    mainScreen{
                        enabled: false
                    }
                    statusBar{
                        loading: true
                    }
                }
            }
        ]
    }
    function log(message) {
        statusBar.text = message
    }
    ReportResultsDialog{
        id: notification
    }
    TableModelProcessor{
        id: modelProcessor
        model: tsvData
        onSuccess: ()=>{
        // onFinished: (success)=>{
        //     print(success)
            notification.open()
            notification.title = "Success"
            notification.text = modelProcessor.report ? modelProcessor.report : "Job finished successfully"
        }
        onErrorOccurred: (message) =>{
            notification.title = "Failed"
            notification.text = "Job was unsuccessful." + message
            notification.open()
        }
        onReportCreated: (message) =>{
            notification.text = message
        }
        enabledActions: [
            // As of 11/20/2026 on PySide6 6.11.2, it is not possible to generate types for ListProperty
            CleanAction{ // qmllint disable missing-property
                actionName: "clean"
            }
        ]
        onProgressChanged: (value) => {
            statusBar.indeterminate = false
            statusBar.progress = value
        }
        onActionLogged: (message, level) => Script.logAction(message, level, Script.ERROR_LEVEL)
    }
    TsvModel{
        id: tsvData
        inspector: inspector
    }
    MetadataEditorScreen {
        objectName: "mainScreen"
        id: mainScreen
        anchors.fill: parent
        model:  tsvData
        onOpenFile: fileName => openTheFile(fileName, mainScreen.dialect ? mainScreen.dialect : Script.determineDialect(fileName), mainScreen.model)
        onProcessData: (request) => {
            const actionName = request.action
            // As of 11/20/2026 on PySide6 6.11.2, it is not possible to generate types for dict types with QtCore.Property
            const action = modelProcessor.actions[actionName] // qmllint disable unresolved-type
            if (action){
                request['action'] = action
                modelProcessor.processData(request)
            }else{
                console.error("action not loaded: " + actionName)
            }
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
    Component.onCompleted: {
        mainScreen.processConfigure.settingsModel.append({"label": "Characters to remove",        "value": "?[]", "variableName": "charactersToRemove",           "delegate": "textEditDelegate"    })
        mainScreen.processConfigure.settingsModel.append({"label": "Remove double dash postfix",  "value": true,  "variableName": "removeDoubleDashPostfix",      "delegate": "booleanDelegate"     })
        mainScreen.processConfigure.settingsModel.append({"label": "Remove trailing periods",     "value": true,  "variableName": "removeTrailingPeriods",        "delegate": "booleanDelegate"     })
        mainScreen.processConfigure.settingsModel.append({"label": "Add comma after space",       "value": true,  "variableName": "addCommaAfterSpace",           "delegate": "booleanDelegate"     })
        mainScreen.processConfigure.settingsModel.append({"label": "Remove trailing punctuation", "value": true,  "variableName": "removeTrailingPunctuation",    "delegate": "booleanDelegate"     })
        mainScreen.processConfigure.settingsModel.append({"label": "Remove duplicate values",     "value": true,  "variableName": "removeDupValues",              "delegate": "booleanDelegate"     })
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
    footer:
        StatusBar{
        id: statusBar
    }
}

