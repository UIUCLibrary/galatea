"""Generate standalone application.

The resulting application does not require the Python Runtime preinstalled
on the user's machine.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   'cmake', 'pip>=26.1', 'tomlkit', 'packaging'
#   ]
# ///

import abc
import argparse
import functools
import hashlib
import importlib.util
import logging
import os.path
import platform
import sys
import tempfile
import venv
import zipfile
from typing import Callable

import pathlib
import shutil
import subprocess
import tomllib
import typing

import cmake
import tomlkit
import packaging.version

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SPECS_TEMPLATE = """# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    %(entry_points)s,
    pathex=%(pathex)s,
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[%(hooks_path)r],
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


def create_standalone(
    pyinstaller_exec,
    specs_file: str,
    dist: str,
    work_path: str
) -> None:
    """Generate standalone executable application."""
    cmd = [
                pyinstaller_exec,
                "--noconfirm",
                specs_file,
                "--distpath",
                dist,
                "--workpath",
                work_path,
                "--clean",
                "--log-level",
                "WARN",
            ]
    subprocess.check_call(cmd)


class ValidatePackage(argparse.Action):
    """Validate package arguments."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values,
        option_string: typing.Optional[str] = None
    ):
        """Validate package arguments."""
        if values is None:
            raise ValueError("missing package")
        values = typing.cast(pathlib.Path, values)
        if not values.exists():
            parser.error(f"'{values}' does not exist.")
        if not values.is_file():
            parser.error(f"'{values}' is not a file.")
        if not values.name.endswith(".whl"):
            parser.error(f"'{values}' is not a wheel")
        setattr(namespace, self.dest, values)


def generate_spec_file(
    output_file: str, script_name: str, entry_point: str, path: str = ""
):
    """Generate pyinstaller specs file."""
    specs = {
        "entry_points": [entry_point],
        "name": script_name,
        "hooks_path": os.path.abspath(
            f"{pathlib.Path(__file__).parent / 'hooks'}"
        ),
        "pathex": [path],
    }
    specs_files = pathlib.Path(output_file)
    dist_path = specs_files.parent
    if not dist_path.exists():
        dist_path.mkdir(parents=True, exist_ok=True)
    specs_files.write_text(SPECS_TEMPLATE % specs, encoding="utf-8")


def get_arg_parser() -> argparse.ArgumentParser:
    """Generate argument parser."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--dest", default="./dist")
    arg_parser.add_argument(
        "--license-file", default="LICENSE", type=pathlib.Path
    )
    arg_parser.add_argument(
        "--include-readme", default="README.md", type=pathlib.Path
    )
    arg_parser.add_argument("--include-tab-completions", action="store_true")
    arg_parser.add_argument(
        "--build", default="./build/standalone_distribution", dest="build_path"
    )
    package_manager_choices = ['pip']
    if shutil.which("uv"):
        package_manager_choices.append('uv')

    arg_parser.add_argument(
        "--package-manager", default="pip", dest="package_manager", choices=package_manager_choices
    )
    arg_parser.add_argument(
        "-r", "--requirements",
        help='-r --requirements <file>    '
             'Install from the given requirements file. '
             'This option can be used multiple times.'
    )
    arg_parser.add_argument(
        "python_package_file",
        type=pathlib.Path,
        action=ValidatePackage,
        help="wheel or source distribution package"
    )
    arg_parser.add_argument("command_name")
    arg_parser.add_argument("entry_point")

    return arg_parser


def find_standalone_distrib(name: str, path: str) -> typing.Optional[str]:
    """Locate a standalone application with a path."""
    for item in os.scandir(path):
        if not item.is_dir():
            continue
        if item.name == name:
            return item.path
    return None


class GenerateCPackConfig(abc.ABC):
    """CPackConfig builder."""

    def __init__(
        self, package_name: str, source_package_path: str, version_number: str
    ):
        """Create a new GenerateCPackConfig builder object."""
        self.source_package_path = source_package_path
        self.install_path_name = "."
        self.metadata = {
            "CPACK_PACKAGE_VERSION": version_number,
        }
        self.package_name = package_name
        self._additional_directories: typing.Set[typing.Tuple[str, str]] = (
            set()
        )

    def add_additional_directories(
        self, source: str, packaged_folder: str
    ) -> None:
        """Add additional directories to install package."""
        self._additional_directories.add((source, packaged_folder))

    def create_boilerplate_config(self) -> str:
        """Generate the boilerplate config lines."""
        version = self.metadata["CPACK_PACKAGE_VERSION"]
        package_description = self.metadata.get(
            "CPACK_PACKAGE_DESCRIPTION", ""
        )
        if not package_description:
            logger.warning("No description provided")

        lines = [
            f'set(CPACK_PACKAGE_NAME "{self.package_name}")',
            f'set(CPACK_PACKAGE_DESCRIPTION "{package_description}")',
            f'set(CPACK_PACKAGE_FILE_NAME "{self.package_name}")',
            f'set(CPACK_PACKAGE_VERSION "{version}")',
        ]
        version_parser = packaging.version.Version(version)
        lines.append(
            f'set(CPACK_PACKAGE_VERSION_MAJOR "{version_parser.major}")'
        )
        lines.append(
            f'set(CPACK_PACKAGE_VERSION_MINOR "{version_parser.minor}")'
        )
        lines.append(
            f'set(CPACK_PACKAGE_VERSION_PATCH "{version_parser.micro}")'
        )
        # Escape backslashes in windows paths
        app_root_dir = os.path.abspath(self.source_package_path).replace(
            "\\", "\\\\"
        )

        def sanitize_path(path: str) -> str:
            return os.path.abspath(path).replace("\\", "\\\\")

        cpack_installed_dirs = " ".join(
            [
                f'"{sanitize_path(source_dir)}" "{package_dir}"'
                for source_dir, package_dir in (
                    {(app_root_dir, self.install_path_name)}.union(
                        self._additional_directories
                    )
                )
            ]
        )
        lines.append(
            f"set(CPACK_INSTALLED_DIRECTORIES {cpack_installed_dirs})"
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
                f'set(CPACK_PACKAGE_DIRECTORY "{sanitize_path(output_path)}")'
            )
        return "\n".join(lines)

    def build(self) -> str:
        """Build the contents of a config file to use with cpack."""
        return "\n".join([self.create_boilerplate_config()])


def package_with_cpack(
    package_name: str,
    build_path: str,
    package_root: str,
    dist: str,
    package_metadata: typing.Dict[str, str],
    cpack_generator: str,
) -> None:
    """Package application using cpack utility, part of CMake."""
    cpack_file = os.path.join(build_path, "CPackConfig.cmake")
    with open(cpack_file, "w", encoding="utf-8") as f:
        cpack_file_generator = GenerateCPackConfig(
            package_name,
            package_root,
            version_number=package_metadata["version"],
        )
        if "output_path" in package_metadata:
            cpack_file_generator.metadata["CPACK_PACKAGE_DIRECTORY"] = (
                package_metadata["output_path"]
            )
        cpack_file_generator.metadata["CPACK_PACKAGE_DESCRIPTION"] = (
            package_metadata.get("description", "")
        )
        f.write(cpack_file_generator.build())
    cpack_cmd = shutil.which("cpack", path=cmake.CMAKE_BIN_DIR)
    if not cpack_cmd:
        raise RuntimeError("unable to locate cpack command")
    subprocess.check_call(
        [cpack_cmd, "--config", cpack_file, "-G", cpack_generator]
    )
    for file in filter(
        lambda item: item.is_file(),
        os.scandir(package_metadata["output_path"]),
    ):
        output_file = os.path.normpath(os.path.join(dist, file.name))
        logger.info("Copying %s to %s", file.name, output_file)
        shutil.copy(file.path, output_file)



def package_with_system_tar(
    package_name: str,
    build_path: str,
    package_root: str,
    dist: str,
    package_metadata: typing.Dict[str, str],
):
    """Package application with the OS's tar file."""
    archive_file_path = os.path.join(
        dist,
        f"{package_name}-{package_metadata['version']}-{package_metadata['os_name']}-{package_metadata['architecture']}.tar.gz",
    )
    archive_root = os.path.join(package_root, "..")
    tar = shutil.which("tar")
    if not tar:
        raise RuntimeError("Could not find tar command on path")
    command = [
        tar,
        "-zcv",
        "-h",
        "-f",
        os.path.relpath(archive_file_path, build_path),
        "-C",
        os.path.abspath(archive_root),
        os.path.relpath(package_root, archive_root),
    ]
    subprocess.check_call(command, cwd=build_path)


def package_with_builtin_zip(
    package_name: str,
    build_path: str,
    package_root: str,
    dist: str,
    package_metadata: typing.Dict[str, str],
) -> None:
    """Package application with the builtin Python zipfile library."""
    zip_file_path = os.path.join(
        dist,
        f"{package_name}-{package_metadata['version']}-{package_metadata['os_name']}-{package_metadata['architecture']}.zip",
    )
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_root):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_path)
                zipf.write(file_path, arcname)

    logger.info("Created %s", zip_file_path)


def package_distribution(
    package_name: str,
    dist: str,
    build_path: str,
    package_root: str,
    metadata_strategy: typing.Callable[[], typing.Dict[str, str]],
    package_strategy: typing.Callable[
        [str, str, str, str, typing.Dict[str, str]], None
    ],
) -> None:
    """Create a distribution package."""
    package_metadata = metadata_strategy()
    package_strategy(
        package_name, build_path, package_root, dist, package_metadata
    )


def create_completions(
    entry_point: str,
    dest: str,
    register_exec="register-python-argcomplete"
) -> None:
    """Create cli tab completion files for shells."""
    command = [register_exec, entry_point]
    if sys.platform == "darwin":
        supported_shells = {
            "bash": {"file_name": f"{entry_point}.d"},
            "zsh": {"file_name": f"_{entry_point}"},
            "fish": {"file_name": f"{entry_point}.uvx.fish@"},
        }
    elif sys.platform == "win32":
        supported_shells = {
            "powershell": {
                "file_name": f"{entry_point.title()}ArgumentCompleter.psm1"
            }
        }
    else:
        supported_shells = {}
    for shell, shell_metadata in supported_shells.items():
        full_command = command + ["--shell", shell]
        result = subprocess.run(full_command, capture_output=True, check=True)
        output_path = os.path.join(dest, shell)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file_name = shell_metadata["file_name"]
        completion_file = os.path.join(output_path, file_name)
        with open(completion_file, "w", encoding="utf-8") as f:
            f.write(result.stdout.decode())


def include_extra_files(
    args: argparse.Namespace,
    dest: typing.Union[typing.LiteralString, str | bytes],
) -> None:
    """Include extra file with the package."""
    if os.path.exists(args.license_file):
        shutil.copy(args.license_file, dest)
    else:
        logger.warning("Unable to locate license file %s.", args.license_file)

    if os.path.exists(args.include_readme):
        logger.debug(
            "Found readme file %s. Including it in package",
            args.include_readme,
        )
        shutil.copy(args.include_readme, dest)


def read_pkg_info(raw_data: str):
    """Read package info."""
    data: typing.Dict[str, typing.Optional[str]] = {
        "name": None,
        "version": None,
        "license": None,
        "summary": None,
        "project_url": None
    }
    for line in raw_data.split("\n"):
        match line.split():
            case ["Name:", name]:
                data["name"] = name

            case ["Version:", version]:
                data["version"] = version

            case ["License-Expression:", license_type]:
                data["license"] = license_type

            case["Summary:", *values]:
                data["summary"] = " ".join(values)

            case["Project-URL:", "project,", url]:
                data["project_url"] = url
    return data


def read_whl_metadata(wheel):
    """Read Whl file metadata."""
    with zipfile.ZipFile(wheel) as zip_file:
        for compressed_file in zip_file.infolist():
            if compressed_file.is_dir():
                continue
            path, filename = os.path.split(compressed_file.filename)
            if "dist-info" not in path.split(os.path.sep)[0]:
                continue
            if "METADATA" != filename:
                continue
            return read_pkg_info(
                zip_file.read(compressed_file).decode("utf-8")
            )
        raise FileNotFoundError("Unable to find whl metadata")


def create_venv_with_venv_package(build_path) -> str:
    """Create a virtual environment using standard venv module.

    Note: there has been problems using this when using a python distribution
     provided from uv.
    """
    venv.create(build_path, with_pip=False, clear=True)
    venv_python = locate_python(build_path)
    if not venv_python:
        raise FileNotFoundError("Virtualenv python not found")
    subprocess.check_call([venv_python, "--version"])
    return venv_python


def create_venv_with_uv_package(build_path) -> str:
    """Create a virtual environment using uv."""
    uv_command = shutil.which("uv")
    if not uv_command:
        raise FileNotFoundError("Uv not found")
    subprocess.check_call(
        [
            uv_command,
            "venv",
            build_path,
            "--python", sys.executable
        ]
    )
    venv_python = locate_python(build_path)
    if not venv_python:
        raise FileNotFoundError("Virtualenv python not found")
    subprocess.check_call([venv_python, "--version"])
    return venv_python


def add_wheel_to_pylock(
    wheel: str,
    src_lockfile: str,
    output_lockfile: str
) -> str:
    """Create a new pylockfile with a reference to the whl file."""
    with open(wheel, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        package_hash = digest.hexdigest()

    with open(src_lockfile, "r", encoding="utf-8") as lock_file_fp:
        lock_file_content = tomlkit.parse(lock_file_fp.read())

    wheel_metadata = read_whl_metadata(wheel)
    new_package = {
        "name": wheel_metadata["name"],
        "version": wheel_metadata["version"],
        "archive": {
            "path": os.path.relpath(
                wheel, start=os.path.dirname(output_lockfile)
            ),
            "hashes": {"sha256": package_hash},
        },
    }
    lock_file_content["packages"].append(new_package)
    with open(output_lockfile, "w", encoding="utf-8") as output_fp:
        output_fp.write(tomlkit.dumps(lock_file_content))
    return output_lockfile


def create_virtualenv_from_pylock(
    package: str,
    build_path: str,
    lock_file: str,
    venv_create_strategy: Callable[[str], str] = create_venv_with_venv_package,
) -> None:
    """Create Python virtual environment using the package provided."""
    venv_python = venv_create_strategy(build_path)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        generated_pylockfile = add_wheel_to_pylock(
            package,
            lock_file,
            os.path.join(tmp_dir_path, "pylock.toml")
        )

        pip_exec = locate_pip(build_path)
        if not pip_exec:
            raise FileNotFoundError("Unable to locate pip executable.")

        args = pip_exec + [
            f"--python={venv_python}",
            "install",
            "--upgrade",
            "-r", generated_pylockfile,
        ]
        subprocess.run(
            args,
            check=True
        )


def locate_python(package_env) -> typing.Optional[str]:
    """Locate python executable in a venv package."""
    possible_locations = [
        os.path.join(package_env, "bin"),
        os.path.join(package_env, "Scripts"),
    ]
    for location in possible_locations:
        command = shutil.which("python", path=location)
        if command:
            return command
    return None


def locate_pyinstaller(package_env):
    """Locate pyinstaller executable."""
    possible_locations = [
        os.path.join(package_env, "bin"),
        os.path.join(package_env, "Scripts")
    ]
    for location in possible_locations:
        pyinstaller = shutil.which("pyinstaller", path=location)
        if pyinstaller:
            return pyinstaller
    return None


def locate_pip(package_env) -> typing.Optional[typing.List[str]]:
    """Locate pip executable."""
    if importlib.util.find_spec("pip") is not None:
        return [sys.executable, "-m", "pip"]

    possible_locations = [
        os.path.join(package_env, "bin"),
        os.path.join(package_env, "Scripts"),
    ]

    for location in possible_locations:
        command = shutil.which("pip", path=location)
        if command:
            return [command]
    return None


def locate_register_python_argcomplete(package_env):
    """Locate register-python-argcomplete command in the current directory."""
    possible_locations = [
        os.path.join(package_env, "bin"),
        os.path.join(package_env, "Scripts"),
    ]

    for location in possible_locations:
        register_arg_complete_command =\
            shutil.which("register-python-argcomplete", path=location)

        if register_arg_complete_command:
            return register_arg_complete_command
    return None


package_manager_venv_strategies: typing.Dict[str, Callable[[str], str]] = {
    "pip": create_venv_with_venv_package,
    "uv": create_venv_with_uv_package,
}


def main() -> None:
    """Start main entry point."""
    args = get_arg_parser().parse_args()
    package_env = os.path.join(args.build_path, "galatea")
    if not os.path.exists(package_env):
        os.makedirs(package_env)

    if venv_strategy := package_manager_venv_strategies.get(
        args.package_manager
    ):
        create_virtualenv_from_pylock(
            args.python_package_file,
            package_env,
            args.requirements,
            venv_create_strategy=venv_strategy
        )
    else:
        raise RuntimeError(f"Unknown package manager: {args.package_manager}")

    pyinstaller = locate_pyinstaller(package_env)
    if not pyinstaller:
        raise FileNotFoundError("Unable to locate pyinstaller")

    specs_file = os.path.join(args.build_path, f"{args.command_name}.spec")
    generate_spec_file(
        specs_file,
        script_name=args.command_name,
        entry_point=os.path.abspath(args.entry_point),
        path=os.path.abspath("src"),
    )
    package_path = os.path.join(args.build_path, "package", args.command_name)
    create_standalone(
        pyinstaller,
        specs_file=specs_file,
        dist=package_path,
        work_path=os.path.join(args.build_path, "work_path"),
    )
    dist = find_standalone_distrib(name=args.command_name, path=package_path)
    if dist is None:
        raise FileNotFoundError("No standalone distribution found")
    include_extra_files(args, dest=package_path)

    def metadata_strategy():
        project_toml_file = "pyproject.toml"
        os_friendly_names = {"Darwin": "MacOS"}
        metadata = {
            "description": "this is a script",
            "output_path": os.path.join(args.build_path, "cpack"),
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

    if args.include_tab_completions:
        register_arg_command = locate_register_python_argcomplete(package_env)
        if not register_arg_command:
            raise FileNotFoundError(
                "Unable to locate register-python-argcomplete"
            )

        create_completions(
            args.command_name,
            os.path.abspath(
                os.path.join(package_path, "extras", "cli_completion")
            ),
            register_exec=register_arg_command
        )
    cpack_generator = "TGZ" if sys.platform == "darwin" else "ZIP"
    package_distribution(
        args.command_name,
        args.dest,
        build_path=args.build_path,
        package_root=os.path.abspath(package_path),
        metadata_strategy=metadata_strategy,
        package_strategy=package_with_system_tar
        if sys.platform == "darwin"
        else functools.partial(
            package_with_cpack,
            cpack_generator=cpack_generator,
        ),
    )


if __name__ == "__main__":
    main()
