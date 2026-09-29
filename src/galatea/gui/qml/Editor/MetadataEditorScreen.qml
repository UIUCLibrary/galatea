import QtQuick
import QtQuick.Dialogs

MetadataEditorScreenForm {
    id: form
    signal saveFileAs(url fileName)
    signal openFile(url fileName)
    property url fileName: ""
    property variant dialect: null
    toolBar.saveButton.enabled: "isModified" in form.model ? form.model.isModified: true
    states: [
        State {
            name: "empty"
            when: form.model.count === 0
        },
        State {
            name: "unmodified"
            when: !form.model.isModified
        },
        State {
            name: "modified"
            when: "isModified" in form.model ? form.model.isModified: true
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
    }
    Connections {
        target: form.toolBar
        function onFileOpenRequested() {
            form.openFileRequested()
        }
    }
    Connections {
        target: form.model
        function onDataChanged() {
            if (form.model.isEmpty) {
                form.state = "empty"
            }
            form.state = form.model.isModified ? "modified" : "unmodified"
        }
    }
    Connections {
        target: form
        function onFileNameChanged() {
            form.openFile(form.fileName)
        }
    }
    Connections {
        target: form
        function onOpenFileRequested() {
            openFileDialog.open()
        }
    }

}