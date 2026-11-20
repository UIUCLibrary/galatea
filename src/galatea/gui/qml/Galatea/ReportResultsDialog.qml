import QtQuick
import QtQuick.Controls

Dialog{
    property alias text: informativeText.text
    id: root
    title: "Job Finished"
    modal: true
    closePolicy: Popup.CloseOnEscape
    implicitWidth: 400
    implicitHeight: 300
    anchors.centerIn: parent
    contentItem: Rectangle {
        color: palette.base

            clip: true
        ScrollView {
            anchors.fill: parent
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            Text {
                id: informativeText
                wrapMode: Text.WordWrap
                text: ""
                color: palette.text
            }
        }
    }
    standardButtons: Dialog.Ok
    onClosed: () =>{
        root.title = "Job Finished"
        informativeText.text = ""
    }
}