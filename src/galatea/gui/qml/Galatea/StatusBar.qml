import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ToolBar {
    id: statusBar
    property alias text: statusBarLabel.text
    property alias logDuration: statusHide.interval
    property alias loading: progressBar.visible
    property alias progress: progressBar.value
    property alias indeterminate: progressBar.indeterminate
    Connections{
        target: statusBar
        function onTextChanged() {
            if (statusBarLabel.text !== ""){
                statusHide.running? statusHide.restart(): statusHide.start()
            }
        }
    }
    ProgressBar{
        id: progressBar
        anchors.fill: parent
        indeterminate: true
        visible: false
        anchors{
            leftMargin: 2
            rightMargin: 2
            topMargin: 2
            bottomMargin: 3
        }
    }
    RowLayout{
        anchors{
            fill: parent
            leftMargin: 10
            rightMargin: 10
            topMargin: 2
            bottomMargin: 2
        }
        Label {
            id: statusBarLabel
            Layout.fillWidth: true
            clip: true
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