import QtQuick
import QtQuick.Dialogs

MetadataEditorScreenForm {
    id: form
    signal saveFileAs(url fileName)
    signal openFile(url fileName)
    signal processData(var processRequest)
    property url fileName: ""
    property variant dialect: null
    property alias tools: form.toolBar

    toolBar{
        // processButton is not visible until process commands has more than just clean
        processButton.visible: false
        cleanButton.enabled: form.state !== "empty"
        saveButton.enabled: form.state === "modified"
    }
    states: [
        State {
            name: "empty"
            when: form.model ? form.model.count === 0 : true
        },
        State {
            name: "loading"
        },
        State {
            name: "unmodified"
        },
        State {
            name: "modified"
        }
    ]
    function handleSaveRequest(){
        if (form.fileName === "") {
            form.saveAs()
        } else {
            console.log(form.fileName)
            console.log("Saving existing file |" + form.fileName + "|")
            form.saveFileAs(form.fileName)
        }
    }

    function saveAs(){
        if (form.state === "empty"){
            console.log("Can not save an empty table")
        } else {
            saveFileDialog.open()
        }
    }
    FileDialog{
        id: openFileDialog
        title: "Please choose a tsv metadata file"
        nameFilters: [ "Tab-Separated Value files files (*.tsv)", "All files (*)" ]
        onAccepted: {
            form.fileName = openFileDialog.selectedFile
        }
    }
    FileDialog{
        id: saveFileDialog
        title: "Please choose a tsv metadata file"
        fileMode: FileDialog.SaveFile
        nameFilters: [ "Tab-Separated Value files files (*.tsv)", "All files (*)" ]
        onAccepted: {
            form.saveFileAs(saveFileDialog.selectedFile);
        }
    }
    ProcessDialog{
        id: processDialogBox
        onProcessRequested: (data) =>{
            form.processData(data)
        }
    }
    Connections {
        target: form.toolBar
        function onFileSaveRequested() {
            form.saveFileRequested()
        }
        function onCleanRequested(){
            form.processData({"action": "clean"})
        }
    }
    Connections {
        target: form
        function onSaveFileRequested() {
            form.handleSaveRequest()
        }
        function onFileNameChanged() {
            form.openFile(form.fileName)
        }
        function onOpenFileRequested() {
            openFileDialog.open()
        }
    }
    Connections {
        target: form.toolBar
        function onProcessRequested(){
            processDialogBox.open()
        }
        function onFileOpenRequested() {
            form.openFileRequested()
        }
    }

}