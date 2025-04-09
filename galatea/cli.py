"""cli interface to galatea."""
# PYTHON_ARGCOMPLETE_OK

import argparse
import contextlib
import pathlib
import sys
from importlib import metadata
import logging
from typing import Optional, List
import typing

import galatea

from galatea import clean_tsv
from galatea import validate_authorized_terms
from galatea import resolve_authorized_terms

import argcomplete

__doc__ = "Galatea is a tool for manipulating tsv data."
__all__ = ["main"]


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
        required=True,
    )

    # --------------------------------------------------------------------------
    #  Clean tsv command
    # --------------------------------------------------------------------------
    clean_tsv_cmd = subparsers.add_parser("clean-tsv", help="clean TSV files")
    clean_tsv_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    clean_tsv_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    clean_tsv_cmd.add_argument(
        "--output",
        dest="output_tsv",
        type=pathlib.Path,
        help="Output tsv file",
    )
    # --------------------------------------------------------------------------
    #  Authority check command
    # --------------------------------------------------------------------------
    authority_check_cmd = subparsers.add_parser(
        "authority-check", help="validate-authorized-names"
    )

    authority_check_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    authority_check_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    # todo: move authority-check into authorized-terms subcommand

    # --------------------------------------------------------------------------
    # authorized-terms command
    # --------------------------------------------------------------------------

    authorized_terms_cmd = subparsers.add_parser(
        "authorized-terms", help="manipulate authorized terms used"
    )
    authorized_terms_parser = authorized_terms_cmd.add_subparsers(
        dest="authorized_term_command", required=True
    )

    authorized_terms_transform_cmd = authorized_terms_parser.add_parser(
        "new-transformation-file", help="create a new transformation tsv file"
    )
    authorized_terms_transform_cmd.add_argument(
        "--output",
        dest="output",
        type=pathlib.Path,
        help="Output tsv file",
        default=pathlib.Path(resolve_authorized_terms.DEFAULT_TRANSFORMATION_FILE_NAME),
    )
    authorized_terms_transform_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    resolve_authorized_terms_cmd = authorized_terms_parser.add_parser(
        "resolve",
        help="resolve unauthorized terms to authorized terms in found tsv file "
    )
    resolve_authorized_terms_cmd.add_argument(
        "transformation_tsv_file",
        type=pathlib.Path,
        help="Transformation tsv file",
    )
    resolve_authorized_terms_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    resolve_authorized_terms_cmd.add_argument(
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
        clean_tsv.logger, verbosity=get_logger_level_from_args(args)
    ):
        clean_tsv.clean_tsv(
            typing.cast(pathlib.Path, args.source_tsv),
            output,
            row_diff_report_generator=clean_tsv.create_diff_report,
        )


def authority_check_command(args: argparse.Namespace) -> None:
    with manage_module_logs(
        validate_authorized_terms.logger,
        verbosity=get_logger_level_from_args(args),
    ):
        validate_authorized_terms.validate_authorized_terms(args.source_tsv)


def resolve_authorized_terms_command(args: argparse.Namespace) -> None:
    with manage_module_logs(
        resolve_authorized_terms.logger,
        verbosity=get_logger_level_from_args(args),
    ):
        resolve_authorized_terms.resolve_authorized_terms(
            input_tsv=args.source_tsv,
            transformation_file=args.transformation_tsv_file,
            output_file=args.output_tsv or args.source_tsv,
        )


def generate_new_transformation_file(args: argparse.Namespace) -> None:
    with manage_module_logs(
        resolve_authorized_terms.logger,
        verbosity=get_logger_level_from_args(args),
    ):
        resolve_authorized_terms.create_init_transformation_file(args.output)


def authorized_terms_command(args: argparse.Namespace):
    match args.authorized_term_command:
        case "resolve":
            resolve_authorized_terms_command(args)
        case "new-transformation-file":
            generate_new_transformation_file(args)
            # print("new-transformation-file")


def main(cli_args: Optional[List[str]] = None) -> None:
    """Run main entry point."""
    arg_parser = get_arg_parser()
    argcomplete.autocomplete(arg_parser)
    args = arg_parser.parse_args(cli_args or sys.argv[1:])

    match args.command:
        case "clean-tsv":
            clean_tsv_command(args)
        case "authority-check":
            authority_check_command(args)
        case "authorized-terms":
            authorized_terms_command(args)
            # resolve_authorized_terms_command(args)


if __name__ == "__main__":
    main()
