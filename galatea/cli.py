"""cli interface to galatea."""

import argparse
import contextlib
import pathlib
import sys
from importlib import metadata
from typing import Optional, List
import typing

import galatea

from galatea import clean_tsv

import logging
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
        title="commands",
        dest="command",
        description="valid commands",
        required=True
    )


    clean_tsv_cmd = subparsers.add_parser("clean-tsv", help="clean TSV files")
    clean_tsv_cmd.add_argument('-v', '--verbose', action='count', default=0, help="increase output verbosity", dest="verbosity")

    clean_tsv_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    clean_tsv_cmd.add_argument(
        "--output",
        dest="output_tsv",
        type=pathlib.Path,
        help="Output tsv file",
    )

    return parser

@contextlib.contextmanager
def manage_module_logs(logger, verbosity=logging.INFO):
    hander = logging.StreamHandler()
    try:
        logger.setLevel(verbosity)
        logger.addHandler(hander)
        yield
    finally:
        logger.removeHandler(hander)

def get_logger_level_from_args(args: argparse.Namespace) -> int:
    try:
        match args.verbosity:
            case 1:
                return galatea.VERBOSE_LEVEL_NUM
            case 2:
                return logging.DEBUG
            case _:
                return logging.INFO
    except AttributeError:
        return logging.INFO

def clean_tsv_command(args: argparse.Namespace) -> None:
    # if no output is explicitly selected, the changes are handled
    # inplace instead of creating a new file

    output: pathlib.Path = args.output_tsv or args.source_tsv

    with manage_module_logs(
        clean_tsv.logger,
        verbosity=get_logger_level_from_args(args)
    ):
        clean_tsv.clean_tsv(
            typing.cast(pathlib.Path, args.source_tsv),
            output,
            row_diff_report_generator=clean_tsv.create_diff_report
        )


def main(cli_args: Optional[List[str]] = None) -> None:
    """Run main entry point."""
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args(cli_args or sys.argv[1:])

    match args.command:
        case "clean-tsv":
            clean_tsv_command(args)


if __name__ == "__main__":
    main()
