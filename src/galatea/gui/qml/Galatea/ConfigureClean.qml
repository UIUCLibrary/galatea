import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window{
    id: root
    width: 640
    height: 480
    visible: true
    signal accepted(var data)
    signal rejected()
    property int labelMargin: 100
    property alias settingsModel: inputModel
    color: palette.window
    onRejected: ()=>{
        close()
    }
    function gatherAndSend(){
        let result = {}
        for(let i = 0; i < inputModel.count; i++){
            const row = inputModel.get(i)
            result[row.variableName] = row.value
        }
        result['action'] = "clean"
        accepted(result)
    }
    onAccepted: ()=>{
        close()
    }
    title: "Cleaning tsv"
    modality: Qt.WindowModal
    ListModel{
        id: inputModel
        dynamicRoles: true
    }
    Component {
        id: textEditDelegate
        TextField {
            text: startingValue ? startingValue : ""
            Layout.fillWidth: true
            onTextEdited: {
                sourceModel.setProperty(itemIndex, "value", text)
            }
        }
    }
    Component {
        id: booleanDelegate
        CheckBox {
            text: label
            checked: startingValue ? startingValue : false
            Layout.fillWidth: true
            onToggled: {
                sourceModel.setProperty(itemIndex, "value", checked)
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        Rectangle{
            color: palette.base
            Layout.fillWidth: true
            Layout.fillHeight: true
            ScrollView {
                anchors{
                    fill: parent
                    topMargin: 2
                    bottomMargin: 2
                    leftMargin: 5
                    rightMargin: 5
                }
                ColumnLayout {
                    anchors{
                        fill: parent
                        leftMargin: 5
                        rightMargin: 5
                    }
                    Repeater {
                        id: repeater
                        model: inputModel
                        delegate: Item{
                            Layout.fillWidth: true
                            height: editedElement.implicitHeight
                            RowLayout {
                                anchors.fill: parent
                                spacing: 35
                                Label {
                                    text: model.delegate === "booleanDelegate" ? "" : model.label
                                    Layout.preferredWidth: labelMargin
                                }
                                Loader{
                                    id: editedElement
                                    property var label: model.label
                                    property var startingValue: model.value
                                    property var sourceModel: repeater.model
                                    property var itemIndex: index
                                    sourceComponent: {
                                        switch(model.delegate){
                                            case "textEditDelegate":
                                                return textEditDelegate
                                            case "booleanDelegate":
                                                return booleanDelegate
                                            default:
                                                console.error('invalid delegate type: "' + model.delegate + '"')
                                                return textEditDelegate
                                        }
                                    }
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
        DialogButtonBox {
            objectName: "buttonBox"
            standardButtons: DialogButtonBox.Ok | DialogButtonBox.Cancel
            Layout.fillWidth: true
            onAccepted: root.gatherAndSend()
            // onAccepted: root.accepted()
            onRejected: root.rejected()
        }
    }
}