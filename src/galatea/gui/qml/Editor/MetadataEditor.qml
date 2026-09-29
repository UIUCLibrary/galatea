pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQml
import "MetadataEditor.js" as Script

Item {
    id: root
    implicitWidth: 600
    implicitHeight: 400
    property alias tableModel: tableView.model
    property alias table: tableView
    property color headingCellColor: palette.button
    property color headingTextColor: palette.buttonText
    property color cellColor: palette.base
    property color cellColorSelected: palette.highlight
    property color cellTextColor: palette.text
    property color borderColor: palette.mid

    Rectangle {
        anchors {
            top: horizontalHeader.top
            left: horizontalHeader.left
            right: root.right
            bottom: horizontalHeader.bottom
        }
        color: root.headingCellColor
    }

    HorizontalHeaderView {
        id: horizontalHeader
        syncView: tableView
        anchors.top: parent.top
        delegate: HeaderDelegate{
            headingCellColor: root.headingCellColor
            id: headerDelegate
            TapHandler{
                onTapped: {
                    Script.selectColumnCells(tableView, headerDelegate.model.column)
                }
            }
        }
    }
    Rectangle{
        anchors{
            top: horizontalHeader.bottom
            bottom: root.bottom
            left: root.left
            right: root.right

        }
        color: palette.base

    }
    TableView{
        id: tableView
        anchors {
            top: horizontalHeader.bottom
            bottom: root.bottom
            left: root.left
            right: root.right
        }
        selectionModel: ItemSelectionModel { model: tableView.model }
        selectionBehavior: TableView.SelectCells
        boundsBehavior: Flickable.StopAtBounds
        editTriggers: TableView.SingleTapped | TableView.EditKeyPressed

        clip: true
        model: SampleModel{}
        SelectionRectangle {
            target: tableView
            selectionMode: SelectionRectangle.Drag
            onDraggingChanged: {
                console.debug("Selection of multiple cells not yet implemented")
            }
            enabled: false
        }
        Keys.onPressed: (event) => Script.handelKeyPressed(event)
        delegate: CellDelegate{
            id: tableCell
            cellColor: Script.chooseBackgroundColor(tableCell, row)
            padding: 2
        }
        ScrollBar.horizontal: ScrollBar {
            policy: ScrollBar.AsNeeded // Options: AlwaysOn, AlwaysOff, AsNeeded
        }
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded // Options: AlwaysOn, AlwaysOff, AsNeeded
        }
        Component.onCompleted: ()=>forceActiveFocus()
        // NOTE: This to be added later
        TapHandler{
            acceptedButtons: Qt.RightButton
            onTapped: {
                if (tableView.selectionModel.selectedIndexes.length === 0) {

                } else {
                    contextMenu.targetRows = tableView.selectionModel.selectedIndexes
                }
                console.debug("context menu is not implemented")
                // contextMenu.popup()
            }
        }
        MetadataEditorContextMenu{
            id: contextMenu
        }
    }
}
