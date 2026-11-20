import QtQuick
import QtTest
import Galatea
Item {

    TestCase{
        name: "TestTableModelProcessor"

        JSProcessAction{
            id: dummyAction
            script: ()=>{
                console.log("do something")
            }
        }

        TableModelProcessor{
            id: modelProcessor
            model: TsvModel{
                id: tsvData
            }
            enabledActions: [
                dummyAction
            ]
        }

        SignalSpy {
            id: dataChangedSpy
            target: tsvData
            signalName: "dataChanged"
        }

        SignalSpy {
            id: modelProcessorErrorSpy
            target: modelProcessor
            signalName: "errorOccurred"
        }
        SignalSpy {
            id: modelProcessorFinishedSpy
            target: modelProcessor
            signalName: "finished"
        }

        function init(){
            backend.load_model_from_file(
                Qt.resolvedUrl("./sample_data.tsv"),
                "excel-tab",
                tsvData
            )
        }

        function test_set_model(){
            verify(modelProcessor.model === tsvData)
        }

        function test_processData_with_valid_action(){
            modelProcessorFinishedSpy.clear()
            verify(modelProcessorFinishedSpy.valid)
            verify(modelProcessorFinishedSpy.count === 0)
            modelProcessor.processData({"action": dummyAction})
            modelProcessor.waitForDone()
            tryVerify(
                function() {
                    return modelProcessorFinishedSpy.count > 0;
                },
                1000
            )
        }

        function test_processData_with_invalid_action(){
            dataChangedSpy.clear()
            modelProcessorErrorSpy.clear()
            verify(dataChangedSpy.count === 0)
            modelProcessor.processData({"action": "not a real function"})
            verify(dataChangedSpy.count === 0)
            verify(modelProcessorErrorSpy.count > 0)
        }
    }
}