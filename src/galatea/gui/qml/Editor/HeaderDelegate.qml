import QtQuick
Item{
    id: root
    property color headingTextColor: palette.buttonText
    // property color headingTextColor: palette.highlightedText
    property color headingCellColor: palette.button
    property color borderColor: palette.mid
    required property var model
    required property var display

    implicitHeight: 35
    implicitWidth: 100
    Rectangle{
        id: rectangle
        color: hoverHandler.hovered ? palette.highlight : root.headingCellColor
        border.color: root.borderColor
        anchors.fill: parent

        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            text: root.display
            clip: true
            anchors.verticalCenter: parent.verticalCenter
            font.bold: true

            // color: hoverHandler.hovered ? palette.highlightedText : palette.brightText

            color: root.headingTextColor // Text color
        }
        HoverHandler {
            id: hoverHandler
        }

    }
}
