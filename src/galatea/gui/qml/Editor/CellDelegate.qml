import QtQuick
import QtQuick.Controls
import "CellDelegate.js" as Script
TableViewDelegate{
    id: tableCell
    implicitWidth: 150
    implicitHeight: 30
    hoverEnabled: true
    background: Rectangle{
        color: Script.chooseBackgroundColor(tableCell)
        border.width: tableCell.current ? 2:1
        border.color: tableCell.current ? palette.highlight: palette.mid

    }
    TableView.editDelegate: TextField {
        required property var model
        required property string display
        id: editField
        text: display
        width: parent.width
        height: parent.height
        focus: true
        onEditingFinished: {
            model.display = text
        }
    }
}
