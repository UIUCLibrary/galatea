import QtQuick

Window {
    width: mainScreen.width < 500 ? 500 : mainScreen.width
    height: mainScreen.height < 100 ? 300 : mainScreen.height
    property string windowTitle: "Metadata Editor"
    property alias model: mainScreen.model
    visible: true
    title: windowTitle
    MetadataEditorScreen {
        id: mainScreen
        anchors.fill: parent
        model:  SampleModel{}
    }
}

