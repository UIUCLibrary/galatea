import QtQuick
import QtQuick.Controls
import "MetadataEditorContextMenu.js" as Script

Menu{
    id: contextMenu
    property var targetRows: []
    MenuItem{
        text: "Run Clean"
        onTriggered: Script.runClean(contextMenu.targetRows)
    }
    MenuItem{
        text: "Check Authorized Terms"
        onTriggered: Script.runCheckAuthorizedTerms(contextMenu.targetRows)
    }
    MenuSeparator { }
    MenuItem{
        text: "Cut"
        onTriggered: Script.runCut(contextMenu.targetRows)
    }
    MenuItem{
        text: "Copy"
        onTriggered: Script.runCopy(contextMenu.targetRows)
    }
    MenuItem{
        text: "Paste"
        onTriggered: Script.runPaste(contextMenu.targetRows)
    }
    MenuItem{
        text: "Delete"
        onTriggered: Script.runDelete(contextMenu.targetRows)
    }
}
