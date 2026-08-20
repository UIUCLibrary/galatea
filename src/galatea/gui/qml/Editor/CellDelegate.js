function onEntered(cellDelegateRect, colors){    cellDelegateRect.color = palette.highlight
    cellDelegateRect.textColor = colors.cellSelectedText
}

function onExited(cellDelegateRect, colors){
    cellDelegateRect.color = colors.cell
}

function onPressed(root, colors){
    console.log("pressed")
    root.selected = !root.selected
}
function chooseBackgroundColor(delegate){
    if( delegate.hovered){
        if (delegate.selected){
            return palette.light
        }
        return palette.midlight
    }
    if (delegate.selected){
        return palette.highlight
    }
    return palette.base
    // return "transparent" // Hover color vs normal color
}