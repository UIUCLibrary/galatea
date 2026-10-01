import argparse
import importlib.resources
import os

from PySide6.QtQuickTest import QUICK_TEST_MAIN


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("qml_file")
    args = parser.parse_args()
    qml_file = args.qml_file
    QUICK_TEST_MAIN(
        "Example test",
        argv=[
            __file__,
            "-import",
            str(importlib.resources.files("galatea.gui.qml")),
            "-input",
            os.path.abspath(qml_file),
            "-functions",
        ],
    )


if __name__ == "__main__":
    main()
