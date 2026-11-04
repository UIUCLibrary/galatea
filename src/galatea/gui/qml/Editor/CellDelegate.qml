import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
TableViewDelegate{
    id: tableCell
    implicitWidth: 150
    implicitHeight: 30
    hoverEnabled: true
    background: Rectangle{
        id: background
        color: palette.base
        border.width: tableCell.current ? 2:1
        border.color: tableCell.current ? palette.highlight: palette.mid
    }
    states: [

        State{
            name: "hovered-and-selected"
            when: tableCell.selected && tableCell.hovered
            PropertyChanges{
                background{
                    color: palette.light
                }
            }
        },
        State{
            name: "modified"
            when: tableCell.model.isModified
            PropertyChanges{
                background{
                    color: palette.accent
                    border.color: palette.highlight
                }
            }
        },
        State{
            name: "hovered"
            when: tableCell.hovered
            PropertyChanges{
                background{
                    color: palette.midlight
                }
            }
        },
        State{
            name: "selected"
            when: tableCell.selected
            PropertyChanges{
                background{
                    color: palette.highlight
                }
            }
        },
    ]
    transitions: [
        Transition {
            to: "*"
            ColorAnimation { target: background; duration: 200}
        }
    ]
    contentItem: Item {
        implicitHeight: 40
        clip: true
        RowLayout {
            anchors.fill: parent
            Text {
                id: displayText
                Layout.leftMargin: 4
                Layout.fillWidth: true
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                // color: palette.highlightedText
                color: palette.text
                text: tableCell.model.display
                font.italic: tableCell.model.isModified
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
