import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
Item {
    id: root
    property alias currentIndex: stack.currentIndex
    property alias count: stack.count
    property var formData: {}

    function next(){
        currentIndex++
    }
    function previous(){
        if(currentIndex > 0) {
            currentIndex--
        }
    }
    ColumnLayout {
        anchors.fill: parent
        StackLayout{
            id: stack
            Layout.fillWidth: true
            Layout.fillHeight: true
            Rectangle {
                color: palette.base
                // color: "#fffae6"
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: "Step 1: Introduction"; font.bold: true; font.pixelSize: 18 }
                    Label { text: "Welcome to the setup wizard." }
                }
            }
            Rectangle {
                color: palette.base
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: "Step 2: Configuration"; font.bold: true; font.pixelSize: 18 }
                }
            }
            Rectangle {
                color: palette.base
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: "Step 3: Summary"; font.bold: true; font.pixelSize: 18 }
                    Label { text: "You are ready to finish!" }
                }
            }
        }
    }
}
