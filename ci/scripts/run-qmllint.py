"""Replacement for pyside6-project qmllint for ci use."""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import glob
from pathlib import Path
import tomllib

import PySide6
from PySide6.scripts import metaobjectdump

PYPROJECT_TOML_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "pyproject.toml"
)
assert os.path.exists(PYPROJECT_TOML_FILE)


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


def add_typeinfo_to_qmldir(location, qmltypes):
    with open(os.path.join(location, "qmldir"), "a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n".join([f"typeinfo {qmltype}" for qmltype in qmltypes]))


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


def get_pyproject_toml_data():
    with open(PYPROJECT_TOML_FILE, "rb") as f:
        return tomllib.load(f)


def get_pyside6_project_files():
    pyproject = get_pyproject_toml_data()
    tools = pyproject.get("tool")
    try:
        if not tools:
            raise KeyError("tool not found")
        pyside_project = tools.get("pyside6-project")
        if not pyside_project:
            raise KeyError("tool.pyside_project not found")
        pyside_files = pyside_project.get("files")
        if not pyside_files:
            raise KeyError("tool.pyside6-project.files not found")
        return pyside_files
    except KeyError:
        print(
            "unable to locate 'tools.pyside6-project.file in pyproject.toml",
            file=sys.stderr,
        )
        return []


def get_qml_files():
    pyside_files = get_pyside6_project_files()
    return [file for file in pyside_files if file.endswith(".qml")]


def python_file_contains_qml_import(file: str) -> bool:
    if not file.endswith(".py"):
        return False
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("QML_IMPORT_NAME"):
                return True
        return False


def get_qml_python_files_with_qml_registered():
    pyside_files = get_pyside6_project_files()
    return [
        pathlib.Path(file)
        for file in pyside_files
        if python_file_contains_qml_import(file)
    ]


def main():
    args = get_arg_parser().parse_args()
    report = args.json
    tmp_dir = args.tmp_dir
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    elements = {}
    for file in get_qml_python_files_with_qml_registered():
        name = os.path.splitext(file.name)[0]
        elements[str(file)] = {
            "name": name,
            "python_file": str(file),
            "metatypes_json": f"{name}metatypes.json",
            "qmltyperegistrations": f"{name}_qmltyperegistrations.cpp",
            "qmltypes": f"{name}.qmltypes",
        }
    for name, metadata in elements.items():
        json_file = os.path.join(tmp_dir, metadata["metatypes_json"])
        run_metaobjectdump(
            [metadata["python_file"]],
            json_file,
        )
    qml_types = [item["qmltypes"] for item in elements.values()]
    #
    # if not os.path.exists(os.path.join(tmp_dir, "Galatea")):
    #     os.makedirs(os.path.join(tmp_dir, "Galatea"))

    shutil.copy(
        "src/galatea/gui/qml/Galatea/qmldir", os.path.join(tmp_dir, "qmldir")
    )
    add_typeinfo_to_qmldir(tmp_dir, qml_types)
    pyside6_path = os.path.dirname(PySide6.__file__)
    print("registering")
    for name, metadata in elements.items():
        qt_tool_wrapper(
            "qmltyperegistrar",
            [
                "--generate-qmltypes",
                os.path.join(tmp_dir, metadata["qmltypes"]),
                "-o",
                os.path.join(tmp_dir, metadata["qmltyperegistrations"]),
                os.path.join(tmp_dir, metadata["metatypes_json"]),
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
    qml_files = get_qml_files()
    for qml_file in qml_files:
        shutil.copyfile(
            qml_file, os.path.join(tmp_dir, os.path.basename(qml_file))
        )

    print("linting", file=sys.stderr)
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
