import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "CellDelegate.js" as Script
TableViewDelegate{
    id: tableCell
    implicitWidth: 150
    implicitHeight: 30
    property alias cellColor: background.color
    property alias indicateModified: displayText.font.italic
    hoverEnabled: true
    background: Rectangle{
        id: background
        color: Script.chooseBackgroundColor(tableCell)
        border.width: tableCell.current ? 2:1
        border.color: tableCell.current ? palette.highlight: palette.mid
    }
    contentItem: Item {
        implicitHeight: 40
        visible: !tableCell.editing
        clip: true
        RowLayout {
            anchors.fill: parent
            Text {
                id: displayText
                Layout.leftMargin: 4
                Layout.fillWidth: true
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                // color: tableCell.indicateModified ? "blue": "red"

                color: tableCell.selected ? palette.highlightedText : palette.highlightedText
                // color: palette.highlightedText
                text: tableCell.model.display
            }
        }
    }
    // TableView.editDelegate: FocusScope{
    //     required property var model
    //     required property string display
    //     width: parent.width
    //     height: parent.height
    //     TableView.onCommit: {
    //         // print("HHHHH")
    //         let qaim = tableCell.tableView.model
    //         if (!qaim)
    //             return
    //         // tableCell.model.font.bold = true
    //         tableCell.model.edit = editField.text
    //     }
    //     TextField {
    //
    //         id: editField
    //         text: display
    //         // width: parent.width
    //         // height: parent.height
    //         anchors.fill: parent
    //         focus: true
    //         onEditingFinished: {
    //             model.display = text
    //         }
    //     }
    // }
}
