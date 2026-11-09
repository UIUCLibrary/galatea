"""Replacement for pyside6-project qmllint for ci use."""

import argparse
import json
import os
import subprocess
import sys
import glob
from pathlib import Path
from PySide6.scripts import metaobjectdump

import PySide6

__all__ = []


def qt_tool_wrapper(qt_tool, args, libexec=False):
    # Taking care of pyside6-uic, pyside6-rcc, and pyside6-designer
    # listed as an entrypoint in setup.py
    pyside_dir = Path(PySide6.__file__).resolve().parent
    if libexec and sys.platform != "win32":
        exe = pyside_dir / "Qt" / "libexec" / qt_tool
    else:
        exe = pyside_dir / qt_tool

    cmd = [os.fspath(exe)] + args
    returncode = subprocess.call(cmd)
    if returncode != 0:
        command = " ".join(cmd)
        print(f"'{command}' returned {returncode}", file=sys.stderr)
    # sys.exit(returncode)


def create_qmldir(location):
    with open(os.path.join(location, "qmldir"), "w", encoding="utf-8") as f:
        f.write("""module Galatea
typeinfo models.qmltypes
""")


def run_metaobjectdump(files, output_file):
    arg_parser = metaobjectdump.create_arg_parser(metaobjectdump.DESCRIPTION)
    args = arg_parser.parse_args([*files, "-o", output_file])

    context = metaobjectdump.VisitorContext()
    json_list = []
    for file_name in args.files:
        file = Path(file_name).resolve()
        if not file.is_file():
            print(
                f"{file_name} does not exist or is not a file.",
                file=sys.stderr,
            )
            raise FileNotFoundError(file_name)

        try:
            json_data = metaobjectdump.parse_file(
                file, context, args.suppress_file
            )
            if json_data:
                json_list.append(json_data)
            elif not args.quiet:
                print(f"No classes found in {file_name}", file=sys.stderr)
        except (AttributeError, SyntaxError) as e:
            reason = str(e)
            print(f"Error parsing {file_name}: {reason}", file=sys.stderr)
            raise

    indent = None if args.compact else 4
    if args.out_file:
        with open(args.out_file, "w") as f:
            json.dump(json_list, f, indent=indent)
    else:
        json.dump(json_list, sys.stdout, indent=indent)


def get_arg_parser():
    parser = argparse.ArgumentParser(description="Run qmllint on QML files")
    parser.add_argument("--json", help="Output JSON report to specified file")
    parser.add_argument(
        "--tmp-dir",
        help="Output JSON report to specified file",
        default=os.path.join("tmp", "Galatea"),
    )
    return parser


def main():
    args = get_arg_parser().parse_args()
    report = args.json
    tmp_dir = args.tmp_dir
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    create_qmldir(tmp_dir)
    run_metaobjectdump(
        ["src/galatea/gui/qml/models.py"],
        os.path.join(tmp_dir, "modelsmetatypes.json"),
    )

    pyside6_path = os.path.dirname(PySide6.__file__)
    print("registering")
    qt_tool_wrapper(
        "qmltyperegistrar",
        [
            "--generate-qmltypes",
            os.path.join(tmp_dir, "models.qmltypes"),
            "-o",
            os.path.join(tmp_dir, "models_qmltyperegistrations.cpp"),
            os.path.join(tmp_dir, "modelsmetatypes.json"),
            "--import-name",
            "Galatea",
            "--major-version",
            "1",
            "--minor-version",
            "0",
            f"--foreign-types={pyside6_path}/Qt/metatypes/qt6core_metatypes.json,{pyside6_path}/Qt/metatypes/qt6qml_metatypes.json",
        ],
        True,
    )
    print("linting", file=sys.stderr)
    qml_files = glob.glob("src/galatea/gui/qml/**/*.qml")
    qmltypes = glob.glob(f"{tmp_dir}/*.qmltypes")

    qmllint_args = (
        ["-i", os.path.join(tmp_dir, "qmldir")] + qmltypes + qml_files
    )
    if report:
        if not os.path.exists(report):
            os.makedirs(os.path.dirname(report), exist_ok=True)
        qmllint_args += ["--json", report]
    qt_tool_wrapper("qmllint", qmllint_args)
    if report:
        print(f"Created report: {report}", file=sys.stderr)


if __name__ == "__main__":
    main()
