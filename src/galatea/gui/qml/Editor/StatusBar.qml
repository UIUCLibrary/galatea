import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ToolBar {
    id: statusBar
    property alias text: statusBarLabel.text
    property alias logDuration: statusHide.interval
    Connections{
        target: statusBar
        function onTextChanged() {
            if (statusBarLabel.text !== ""){
                statusHide.running? statusHide.restart(): statusHide.start()
            }
        }
    }
    RowLayout{
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        Label {
            id: statusBarLabel
            Layout.fillWidth: true
            color: palette.windowText
            font.pixelSize: 12
            Timer{
                id: statusHide
                interval: 2000
            }
            states: [
                State {
                    name: "newMessage"
                    when: statusHide.running
                    PropertyChanges { statusBarLabel.opacity: 100 }
                },
                State {
                    name: "stale"
                    when: !statusHide.running
                    PropertyChanges { statusBarLabel.opacity: 0 }
                },
            ]
            transitions: [
                Transition{
                    NumberAnimation { properties: "opacity"; easing.type: Easing.InOutQuad; duration: 150 }
                }
            ]
        }
    }
    Component.onDestruction: {
        statusHide.stop()
    }
}