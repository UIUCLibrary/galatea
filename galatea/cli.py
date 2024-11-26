"""cli interface to galatea."""

import argparse
import pathlib
import sys
from importlib import metadata
from typing import Optional, List
import typing
from galatea import clean_tsv, add_authorities

__doc__ = "Galatea is a tool for manipulating tsv data."
__all__ = ['main']


def get_versions_from_package() -> Optional[str]:
    """Get version information from the package metadata."""
    try:
        return metadata.version(__package__)
    except metadata.PackageNotFoundError:
        return None


DEFAULT_VERSION_STRATEGIES = [get_versions_from_package]


def get_version() -> str:
    """Get the version of current application."""
    for strategy in DEFAULT_VERSION_STRATEGIES:
        version = strategy()
        if version:
            return version
    return "unknown version"


def get_arg_parser() -> argparse.ArgumentParser:
    """Argument parser for galatea cli."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", description="valid commands"
    )

    clean_tsv_cmd = subparsers.add_parser("clean-tsv", help="clean TSV files")

    clean_tsv_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    clean_tsv_cmd.add_argument(
        "--output",
        dest="output_tsv",
        type=pathlib.Path,
        help="Output tsv file",
    )

    add_authorities_cmd = subparsers.add_parser("add-authorities")
    add_authorities_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    add_authorities_cmd.add_argument(
        "--output",
        dest="output_tsv",
        type=pathlib.Path,
        help="Output tsv file",
    )

    return parser


def clean_tsv_command(args: argparse.Namespace) -> None:
    # if no output is explicitly selected, the changes are handled
    # inplace instead of creating a new file
    output: pathlib.Path = args.output_tsv or args.source_tsv
    clean_tsv.clean_tsv(typing.cast(pathlib.Path, args.source_tsv), output)


def add_authorities_command(args: argparse.Namespace):
    output: pathlib.Path = args.output_tsv or args.source_tsv
    add_authorities.add_authorities(typing.cast(pathlib.Path, args.source_tsv), output)



def main(cli_args: Optional[List[str]] = None) -> None:
    """Run main entry point."""
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args(cli_args or sys.argv[1:])

    match args.command:
        case "clean-tsv":
            clean_tsv_command(args)
        case "add-authorities":
            add_authorities_command(args)


if __name__ == "__main__":
    main()
