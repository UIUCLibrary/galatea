function columnWidthProvider(column, tableView){

    let explicitW = tableView.explicitColumnWidth(column);
    if (explicitW >= 0){
        return explicitW;
    }
    if (column === tableView.columns - 1) {
        let usedWidth = 0;
        for (let i = 0; i < column; ++i) {
            usedWidth += tableView.columnWidthProvider(i);
        }
        return Math.max(100, tableView.width - usedWidth);
    }
    return 120;
}

function selectColumnCells(tableView, column){
    let targetIndex = tableView.model.index(0, column)
        tableView.selectionModel.select(targetIndex,
                ItemSelectionModel.ClearAndSelect | ItemSelectionModel.Columns)
}
function handelKeyPressed(event){
    if (event.key === Qt.Key_Escape) {
        event.accepted = handleEscape(tableView)
    }
}
function handleEscape(tableView){
    if (tableView.selectionModel) {
        const index = (tableView.selectionModel.selectedIndexes.length > 0) ? tableView.selectionModel.selectedIndexes[0] : null
        if(!index){
            return false
        }
        tableView.selectionModel.clear()
        tableView.selectionModel.setCurrentIndex(index, ItemSelectionModel.Current | ItemSelectionModel.ClearAndSelect)
    }
    return true
}