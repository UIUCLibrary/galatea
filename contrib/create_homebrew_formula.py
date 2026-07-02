# /// script
# dependencies = [
#   "Jinja2",
# ]
# ///
import argparse
import enum
import hashlib
import os
import sys
import tarfile
import tomllib
from dataclasses import dataclass, field, asdict
from typing import TypedDict, List

import jinja2

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "galatea_formula.rb.jinja2")

class GitInfo(TypedDict):
    head: str
    branch: str

class DependencyType(enum.Enum):
    BUILD = 'build'
    INSTALL = 'install'
    TEST = 'test'

@dataclass
class Dependency:
    dependency: str
    dependency_type: DependencyType = DependencyType.INSTALL

@dataclass
class Resource:
    name: str
    url: str
    sha256: str

@dataclass
class FormulaInfo:
    name: str
    desc : str
    homepage : str
    url : str
    sha256 : str
    license : str
    git_info : GitInfo
    resources : List[Resource] = field(default_factory=list)
    depends_on: List[Dependency] = field(default_factory=list)


def read_pkg_info_fp(file_pointer):
    data = {
        "name": None,
        "version": None,
        "license": None,
        "summary": None,
        "project_url": None
    }
    for line in file_pointer.read().decode("utf-8").split("\n"):
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

def get_package_info(tarball_location):
    metadata = {
        "sha256": None
    }

    with open(tarball_location, 'rb', buffering=0) as f:
        metadata['sha256'] = hashlib.file_digest(f, "sha256").hexdigest()

    with tarfile.open(tarball_location, "r:gz") as tar:
        for member in tar.getmembers():
            location, name = os.path.split(member.name)
            if member.isdir():
                continue

            # PKG-INFO is found one level deep in something like uiucprescon_tripwire-0.3.8
            if len(location.split(os.sep)) > 1:
                continue
            if name != "PKG-INFO":
                continue
            with tar.extractfile(member) as f:
                return {**metadata, **read_pkg_info_fp(f)}

        raise ValueError("no PKG-INFO found")

def get_lock_file_packages(lockfile_path):
    packages = {}
    with open(lockfile_path, "rb") as f:
        data = tomllib.load(f)

    for package in data['packages']:

        if 'marker' in package:
            if "sys_platform == 'win32'" in package['marker']:
                continue
            if "sys_platform == 'linux'" in package['marker']:
                continue

        if "directory" in package:
            continue

        packages[package['name']] = {
            k: v for k, v in package.items() if k not in ("name", "wheels")
        }
    return packages

def render_formula(data) -> str:
    with open(TEMPLATE_FILE) as f:
        template = jinja2.Template(
            f.read(),
        )
        template.globals["DependencyType"] = DependencyType
        return template.render(**asdict(data))

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "sdist",
        help="path to tar.gz sdist file. "
             "For example: galatea-0.5.3.dev0.tar.gz"
    )

    parser.add_argument(
        "lockfile",
        help="path to pylock.toml lockfile. For example pylock.toml",
    )

    parser.add_argument("url", help="url to sdist package stored on internet")

    return parser

def validate_args(args):
    issues = []

    if not os.path.isfile(args.sdist):
        issues.append(f"sdist does not exist")

    if not os.path.isfile(args.lockfile):
        issues.append(f"lockfile does not exist")

    return issues

def main():
    args = get_args().parse_args()

    if issues := validate_args(args):
        sys.stdout.flush()
        for issue in issues:
            print(issue, file=sys.stderr)
        exit(1)

    info = get_package_info(args.sdist)
    lockfile_packages = get_lock_file_packages(args.lockfile)

    print(
        render_formula(
            FormulaInfo(
                name="Galatea",
                desc=info['summary'],
                homepage="https://github.com/UIUCLibrary/galatea",
                url=args.url,
                sha256=info['sha256'],
                license=info['license'],
                git_info={
                    "head": "https://github.com/UIUCLibrary/galatea.git",
                    "branch": "main"
                },
                depends_on=[
                    Dependency("python@3.13"),
                ],
                resources=sorted(
                    [
                        Resource(
                            name=pkg_name,
                            url=pkg_data['sdist']['url'],
                            sha256=pkg_data['sdist']['hashes']['sha256']
                        ) for pkg_name, pkg_data in lockfile_packages.items()
                    ],
                    key=lambda r: r.name
                )
            )
        )
    )

if __name__ == '__main__':
    main()