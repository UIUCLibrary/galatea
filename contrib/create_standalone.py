# /// script
# requires-python = ">=3.11"
# dependencies = [
#   'PyInstaller', 'cmake'
#   ]
# ///

import abc
import argparse
import logging
import os.path
import platform
import sys
import zipfile

import packaging.version
import pathlib
import shutil
import subprocess
import tomllib
import typing
import PyInstaller.__main__
import cmake


SPECS_TEMPLATE = """# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    %(entry_points)s,
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['%(hooks_path)s'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='%(name)s',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='%(name)s',
)
    """

logger = logging.getLogger(__name__)

def create_standalone(specs_file, dist, work_path) -> str:

    PyInstaller.__main__.run([
        '--noconfirm',
        specs_file,
        "--distpath", dist,
        "--workpath", work_path,
        "--clean",
        "--log-level", "WARN"
    ])

def generate_spec_file(output_file: str, script_name: str, entry_point: str):

    specs = {
        "entry_points": [entry_point],
        "name": script_name,
        "hooks_path": pathlib.Path(__file__).parent / "hooks"
    }
    specs_files = pathlib.Path(output_file)
    dist_path = specs_files.parent
    if not dist_path.exists():
        dist_path.mkdir(parents=True, exist_ok=True)
    specs_files.write_text(SPECS_TEMPLATE % specs)

def get_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--dest", default="./dist")
    arg_parser.add_argument("--build", default="./build/standalone_distribution", dest="build_path")
    arg_parser.add_argument("command_name")
    arg_parser.add_argument("entry_point")

    return arg_parser


def find_standalone_distrib(name: str, path: str) -> typing.Optional[str]:
    for item in os.scandir(path):
        if not item.is_dir():
            continue
        if item.name == name:
            return item.path
    return None


class GenerateCPackConfig(abc.ABC):
    def __init__(self, source_package_path: str, version_number: str):
        self.source_package_path = source_package_path
        self.install_path_name = os.path.split(source_package_path)[-1]
        self.metadata = {
            "CPACK_PACKAGE_VERSION": version_number,
        }

    def create_boilerplate_config(self) -> str:
        cpack_package_name = "galatea"
        version = self.metadata["CPACK_PACKAGE_VERSION"]
        package_description = self.metadata.get("CPACK_PACKAGE_DESCRIPTION", "")
        if package_description == "":
            logger.warning("No description provided")

        lines = [
            f'set(CPACK_PACKAGE_NAME "{cpack_package_name}")',
            f'set(CPACK_PACKAGE_DESCRIPTION "{package_description}")',
            f'set(CPACK_PACKAGE_FILE_NAME "{cpack_package_name}")',
            f'set(CPACK_PACKAGE_VERSION "{version}")',
        ]
        version_parser = packaging.version.Version(version)
        lines.append(f'set(CPACK_PACKAGE_VERSION_MAJOR "{version_parser.major}")')
        lines.append(f'set(CPACK_PACKAGE_VERSION_MINOR "{version_parser.minor}")')
        lines.append(f'set(CPACK_PACKAGE_VERSION_PATCH "{version_parser.micro}")')

        lines.append(
            f'set(CPACK_INSTALLED_DIRECTORIES "{os.path.abspath(self.source_package_path)}" "{self.install_path_name}")'
        )
        if sys.platform == "darwin":
            lines.append(
                'set(CPACK_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}-MacOS-${CMAKE_HOST_SYSTEM_PROCESSOR}")'
            )
        else:
            lines.append(
                'set(CPACK_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}-Windows-${CMAKE_HOST_SYSTEM_PROCESSOR}")'
            )


        if "CPACK_PACKAGE_DIRECTORY" in self.metadata:
            output_path = self.metadata["CPACK_PACKAGE_DIRECTORY"]
            lines.append(
                f'set(CPACK_PACKAGE_DIRECTORY "{output_path}")'
            )
        return "\n".join(lines)

    def build(self) -> str:
        return "\n".join([self.create_boilerplate_config()])


def package_with_cpack(build_path, dist, package_metadata, cpack_generator):
    cpack_file = os.path.join(build_path, "CPackConfig.cmake")

    with open(cpack_file, "w") as f:
        cpack_file_generator = GenerateCPackConfig(
            dist, version_number=package_metadata["version"]
        )
        if "output_path" in package_metadata:
            cpack_file_generator.metadata["CPACK_PACKAGE_DIRECTORY"] = package_metadata[
                "output_path"
            ]
        cpack_file_generator.metadata["CPACK_PACKAGE_DESCRIPTION"] = (
            package_metadata.get("description", "")
        )
        f.write(cpack_file_generator.build())
    cpack_cmd = shutil.which("cpack", path=cmake.CMAKE_BIN_DIR)
    subprocess.check_call([cpack_cmd, "--config", cpack_file, "-G", cpack_generator])


def package_with_system_zip(build_path, dist, package_metadata):
    zip_file_path = os.path.join(
        "dist",
        f"avtool-{package_metadata['version']}-{package_metadata['os_name']}-{package_metadata['architecture']}.zip",
    )
    cwd = "dist"
    zip_command = [
        "zip",
        "--symlinks",
        "-r",
        os.path.relpath(zip_file_path, cwd),
        os.path.relpath(dist, cwd),
    ]

    subprocess.check_call(zip_command, cwd=cwd)
    print(f"Created {zip_file_path}")


def package_with_system_tar(build_path, dist, package_metadata):
    archive_file_path = os.path.join(
        "dist",
        f"avtool-{package_metadata['version']}-{package_metadata['os_name']}-{package_metadata['architecture']}.tar.gz",
    )
    cwd = "dist"
    command = [
        "tar",
        "-zcvf",
        # "--keep-directory-symlink",
        os.path.relpath(archive_file_path, cwd),
        "-h",
        os.path.relpath(dist, cwd),
    ]
    subprocess.check_call(command, cwd=cwd)


def package_with_builtin_zip(build_path, dist, package_metadata):
    zip_file_path = os.path.join(
        "dist",
        f"avtool-{package_metadata['version']}-{package_metadata['os_name']}-{package_metadata['architecture']}.zip",
    )
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_path)
                zipf.write(file_path, arcname)

    print(f"Created {zip_file_path}")


def package_distribution(dist, build_path, metadata_strategy, package_strategy):
    package_metadata = metadata_strategy()
    package_strategy(build_path, dist, package_metadata)


def main():
    args = get_arg_parser().parse_args()
    specs_file = os.path.join(args.build_path, f"{args.command_name}.spec")
    generate_spec_file(
        specs_file,
        script_name=args.command_name,
        entry_point=os.path.abspath(args.entry_point),
    )
    create_standalone(
        specs_file, dist=args.dest, work_path=os.path.join(args.build_path, "work_path")
    )
    dist = find_standalone_distrib(name=args.command_name, path=args.dest)
    if dist is None:
        raise FileNotFoundError("No standalone distribution found")

    def metadata_strategy():
        project_toml_file = "pyproject.toml"
        os_friendly_names = {"Darwin": "MacOS"}
        metadata = {
            "description": "this is a script",
            "output_path": args.dest,
            "architecture": platform.machine(),
            "os_name": os_friendly_names[platform.system()]
            if platform.system() in os_friendly_names
            else platform.system(),
        }

        with open(project_toml_file, "rb") as f:
            toml = tomllib.load(f)
            project = toml.get("project", {})
            version = project.get("version")
            if version:
                metadata["version"] = version
            return metadata

    package_distribution(
        dist,
        build_path=args.build_path,
        metadata_strategy=metadata_strategy,
        # package_strategy=package_with_system_zip
        # if sys.platform == "darwin"
        # else package_with_builtin_zip,
        package_strategy=package_with_system_tar
        if sys.platform == "darwin"
        else lambda build_path, dist, package_metadata: package_with_cpack(
            build_path,
            dist,
            package_metadata,
            "TGZ" if sys.platform == "darwin" else "ZIP",
        ),
    )


if __name__ == "__main__":
    main()
