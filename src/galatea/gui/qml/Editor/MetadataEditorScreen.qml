import QtQuick
import QtQuick.Dialogs

MetadataEditorScreenForm {
    id: form
    signal saveFileAs(url fileName)
    signal openFile(url fileName)
    signal processData(var processRequest, var model)
    property url fileName: ""
    property variant dialect: null

    // processButton is not visible until process commands has more than just clean
    toolBar.processButton.visible: false

    toolBar.cleanButton.enabled: form.state !== "empty"
    toolBar.saveButton.enabled: form.state === "modified"
    states: [
        State {
            name: "empty"
            when: form.model.count === 0
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
            form.processData(data, form.model)
        }
    }
    Connections {
        target: form.toolBar
        function onFileSaveRequested() {
            form.saveFileRequested()
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