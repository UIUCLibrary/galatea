import QtQuick
import QtTest
import Editor
Item{
    App{
        id: app
        TestCase {
            name: "Example test"
            function init(){
                app.windowTitle = "Initial Title"

            }
            function test_window_title_can_change(){
                verify( app.windowTitle !== "Test")
                app.windowTitle = "Test"
                compare(app.windowTitle, "Test", "windowTitle should be able to update")
            }
        }
    }
}
