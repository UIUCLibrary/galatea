import argparse
import os
import importlib.resources
import sys

from PySide6 import QtCore, QtQml, QtQuickTest
from galatea.gui.qml import backend


class MyTestSetup(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        # This magic slot name is called automatically by the test framework

    @QtCore.Slot(QtQml.QQmlEngine)
    def qmlEngineAvailable(self, qmlEngine: QtQml.QQmlEngine):
        # Instantiate your backend
        self.backend = backend.Backend()
        context = qmlEngine.rootContext()
        # Inject it into the root context so all QML tests can see it
        context.setContextProperty("backend", self.backend)

        def cleanup():
            print("destroyed", file=sys.stderr)
            print("waiting for threads", file=sys.stderr)
            QtCore.QThreadPool.globalInstance().waitForDone()
            print("waiting for threads -Done", file=sys.stderr)

        context.destroyed.connect(cleanup)
        QtCore.QCoreApplication.processEvents()

        #
        # # app = QtCore.QCoreApplication.instance()
        # # # app.aboutToQuit.connect(qmlEngine.deleteLater)
        # # app.aboutToQuit.connect(waitForThreads)
        # print("Setting threads to highest priority")
        # QtCore.QThreadPool.globalInstance().setThreadPriority(
        #     QtCore.QThread.Priority.HighestPriority
        # )
        # QtCore.QCoreApplication.processEvents()


def run_test(qml_file: str, test_name=None, output_file=None) -> int:
    args = [
        __file__,
        # "-silent",
        "-v2",
        "-import",
        str(importlib.resources.files("galatea.gui.qml")),
        "-input",
        qml_file,
    ]
    if test_name is not None:
        args.append(test_name)
    if output_file is not None:
        args += ["-o", f"{output_file},txt"]
    return QtQuickTest.QUICK_TEST_MAIN_WITH_SETUP(
        str(qml_file), MyTestSetup, argv=args
    )


def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("qml_file", type=str)
    parser.add_argument("--test-name", type=str)
    parser.add_argument("--report_file_name", type=str)
    return parser


default_qml_search_paths = [
    os.getcwd(),
    os.path.abspath(os.path.join(os.path.dirname(__file__))),
]


def locate_test_file_full_path(qml_file, search_paths=None):
    search_paths = (
        search_paths if search_paths is not None else default_qml_search_paths
    )
    for search_path in search_paths:
        candidate_file = os.path.join(search_path, qml_file)
        if os.path.exists(candidate_file):
            return candidate_file
    raise FileNotFoundError(qml_file)


def main():

    parser = get_arg_parser()
    args = parser.parse_args()
    qml_test_file = locate_test_file_full_path(args.qml_file)
    sys.exit(run_test(qml_test_file, args.test_name, args.report_file_name))


if __name__ == "__main__":
    main()
