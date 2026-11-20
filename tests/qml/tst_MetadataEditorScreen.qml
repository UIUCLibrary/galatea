import QtQuick
import QtTest
import Galatea
Item{
    MetadataEditorScreen{
        id: editorScreen
    }
    TestCase{
        name: "MetadataEditorScreen"

        SignalSpy {
            id: mySpy
            target: editorScreen
            signalName: "openFile"
        }

        function test_open_file(){
            mySpy.clear();
            verify(mySpy.count === 0);
            editorScreen.openFile(Qt.resolvedUrl("test.tsv"))
            verify(mySpy.count === 1);
        }
    }
}