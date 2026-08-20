import QtQuick
import Qt.labs.qmlmodels
// Item{
//     id: metadataModel
    TableModel {
       // Define your headers and mapping keys
       TableModelColumn {
           display: "Name"
       }
       TableModelColumn {
           display: "Age"
       }
       TableModelColumn {
           display: "Role"
       }

       // Define your row data blocks
       rows: [{
               "Name": "Alice Smith",
               "Age": 28,
               "Role": "Engineer"
           }, {
               "Name": "Bob Jones",
               "Age": 34,
               "Role": "Designer"
           }, {
               "Name": "Charlie Brown",
               "Age": 22,
               "Role": "Intern"
           }, {
               "Name": "Diana Prince",
               "Age": 31,
               "Role": "Manager"
           }]
   }
// }