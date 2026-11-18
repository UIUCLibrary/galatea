import QtQuick
import QtQuick.Dialogs
import QtQuick.Controls
import QtQuick.Layouts

Dialog{
    id: processDialogBox
    signal processRequested(var requestData)
    title: "Process Data"
    anchors.centerIn: parent
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape
    implicitWidth: 350
    implicitHeight: 350
    contentItem: ProcessAllData {
        id: processAllData
        anchors.fill: parent
    }
    onAccepted:{
        processRequested(processAllData.formData)
    }
    onClosed:{
        processAllData.currentIndex = 0
    }
    footer: DialogButtonBox {
        standardButtons: DialogButtonBox.Cancel | DialogButtonBox.Reset
        Button{
            Layout.alignment: Qt.AlignLeft
            text: "Back"
            enabled: processAllData.currentIndex > 0
            onClicked: {
                processAllData.previous()
            }
        }
        Button{
            Layout.alignment: Qt.AlignRight
            text: ((processAllData.currentIndex + 1) < processAllData.count) ? "Next" : "Process"
            onClicked: {
                if(processAllData.currentIndex + 1 == processAllData.count){
                    processDialogBox.accept()
                }
                if((processAllData.currentIndex + 1) < processAllData.count){
                    processAllData.next()
                }
            }
        }
        alignment: Qt.AlignHCenter
        onReset:{
            processAllData.currentIndex = 0
        }
    }
}