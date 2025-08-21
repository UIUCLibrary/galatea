"""cli interface to galatea."""
# PYTHON_ARGCOMPLETE_OK

import argparse
import contextlib
import dataclasses
import pathlib
import sys
from importlib import metadata
import logging
from typing import Optional, List, Callable
import typing

import galatea
import galatea.config

from galatea import clean_tsv
from galatea import validate_authorized_terms
from galatea import resolve_authorized_terms
from galatea import merge_data

import argcomplete

__doc__ = "Galatea is a tool for manipulating tsv data."
__all__ = ["main"]

logger = logging.getLogger(__name__)


def get_versions_from_package() -> Optional[str]:
    """Get version information from the package metadata."""
    if not __package__:
        return None

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


class ValidateFilePath(argparse.Action):
    """Custom action to validate file paths."""

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(values, pathlib.Path):
            raise argparse.ArgumentTypeError(
                f"Expected a file path, got {values!r}"
            )
        if not values.exists():
            raise argparse.ArgumentTypeError(f"File does not exist: {values}")
        setattr(namespace, self.dest, values.resolve())


def get_arg_parser() -> argparse.ArgumentParser:
    """Argument parser for galatea cli."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )
    default_config_file = galatea.config.get_default_config_file_path()
    parser.add_argument(
        "--config",
        dest="config_file",
        type=pathlib.Path,
        help=f'Path to config file. Default: "{default_config_file}"',
        default=default_config_file,
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

    # --------------------------------------------------------------------------
    # authorized-terms command
    # --------------------------------------------------------------------------

    authorized_terms_cmd = subparsers.add_parser(
        "authorized-terms", help="manipulate authorized terms used"
    )
    authorized_terms_parser = authorized_terms_cmd.add_subparsers(
        dest="authorized_term_command", required=True
    )

    # --------------------------------------------------------------------------
    # authorized-terms check command
    # --------------------------------------------------------------------------

    authorized_terms_check_cmd = authorized_terms_parser.add_parser(
        "check", help="Check authorized terms are used in tsv file"
    )

    authorized_terms_check_cmd.add_argument(
        "source_tsv", type=pathlib.Path, help="Source tsv file"
    )

    authorized_terms_check_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    # --------------------------------------------------------------------------
    # authorized-terms new-transformation-file command
    # --------------------------------------------------------------------------

    authorized_terms_new_transform_file_cmd = (
        authorized_terms_parser.add_parser(
            "new-transformation-file",
            help="create a new transformation tsv file",
        )
    )
    authorized_terms_new_transform_file_cmd.add_argument(
        "--output",
        dest="output",
        type=pathlib.Path,
        help="Output tsv file",
        default=pathlib.Path(
            resolve_authorized_terms.DEFAULT_TRANSFORMATION_FILE_NAME
        ),
    )
    authorized_terms_new_transform_file_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    # --------------------------------------------------------------------------
    # authorized-terms resolve command
    # --------------------------------------------------------------------------
    resolve_authorized_terms_cmd = authorized_terms_parser.add_parser(
        "resolve",
        help="resolve unauthorized terms to authorized terms in found tsv "
        "file",
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

    resolve_authorized_terms_cmd.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
        dest="verbosity",
    )

    # --------------------------------------------------------------------------
    #  merge-data command
    # --------------------------------------------------------------------------
    merge_data_cmd = subparsers.add_parser(
        "merge-data", help="merge data from another source to tsv file"
    )
    merge_data_parser = merge_data_cmd.add_subparsers(
        dest="merge_data_command", required=True
    )

    # --------------------------------------------------------------------------
    #  merge-data.from-getmarc command
    # --------------------------------------------------------------------------
    merge_from_getmarc_cmd = merge_data_parser.add_parser(
        "from-getmarc", help="merge data from getmarc server to tsv file"
    )

    merge_get_marc_data_parser = merge_from_getmarc_cmd.add_subparsers(
        dest="from_getmarc_data_command", required=True
    )

    # --------------------------------------------------------------------------
    #  merge-data.from-get-marc.init_mapping command
    # --------------------------------------------------------------------------
    init_mapping = merge_get_marc_data_parser.add_parser(
        "init-mapper", help="create initial mapping file"
    )
    init_mapping.add_argument(
        "source_tsv_file",
        type=pathlib.Path,
        action=ValidateFilePath,
        help="Source tsv file",
    )

    init_mapping.add_argument(
        "--output_file",
        type=pathlib.Path,
        help="Output file",
        default=pathlib.Path("mapping.toml"),
    )

    merge_merge_from_get_marc_cmd = merge_get_marc_data_parser.add_parser(
        "merge",
        help="merge data from get-marc server and map to tsv file",
        allow_abbrev=False,
    )
    merge_merge_from_get_marc_cmd.add_argument(
        "metadata_tsv_file", type=pathlib.Path, help="tsv file with metadata"
    )
    merge_merge_from_get_marc_cmd.add_argument(
        "--output-tsv-file",
        type=pathlib.Path,
        help="write changes to another file instead of inplace",
    )
    merge_merge_from_get_marc_cmd.add_argument(
        "mapping_file", type=pathlib.Path, help="Mapping file"
    )
    try:
        default_get_marc_server = (
            galatea.config.get_config().get_marc_server_url
        )
    except FileNotFoundError:
        default_get_marc_server = None

    merge_merge_from_get_marc_cmd.add_argument(
        "--getmarc-server",
        type=str,
        help=f'get-marc server url. Default: "{default_get_marc_server}"'
        if default_get_marc_server
        else "get-marc server url.",
        default=default_get_marc_server,
    )

    merge_merge_from_get_marc_cmd.add_argument(
        "--enable-experimental-features",
        action="store_true",
        default=False,
        help="enable experimental features",
    )

    # --------------------------------------------------------------------------
    #  config command
    # --------------------------------------------------------------------------
    config_sub_command = subparsers.add_parser(
        "config", help="configure galatea"
    )
    config_sub_command_parser = config_sub_command.add_subparsers(
        dest="config_command", required=True
    )

    # --------------------------------------------------------------------------
    #  config.set command
    # --------------------------------------------------------------------------
    set_config_subcommand = config_sub_command_parser.add_parser(
        "set", help="set config"
    )
    set_config_subcommand.add_argument(
        "key",
        help="configuration key",
        choices=[
            field.name for field in dataclasses.fields(galatea.config.Config)
        ],
    )
    set_config_subcommand.add_argument("value", help="configuration value")

    # --------------------------------------------------------------------------
    #  config.show command
    # --------------------------------------------------------------------------
    config_sub_command_parser.add_parser(
        "show", help="show current configuration"
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
        case "check":
            authority_check_command(args)


def merge_data_command(args: argparse.Namespace):
    match args.merge_data_command:
        case "from-getmarc":
            merge_get_marc_data_command(args)
        case _:
            raise ValueError(f"unknown command: {args.merge_data_command}")


def merge_from_getmarc(
    metadata_tsv_file,
    output_tsv_file,
    mapping_file,
    getmarc_server,
    enable_experimental_features: bool,
) -> None:
    try:
        merge_data.merge_from_getmarc(
            input_metadata_tsv_file=metadata_tsv_file,
            output_metadata_tsv_file=output_tsv_file,
            mapping_file=mapping_file,
            get_marc_server=getmarc_server,
            enable_experimental_features=enable_experimental_features,
        )
    except merge_data.ExperimentalFeatureError as e:
        print(
            "Error: attempting to use a feature that is listed as "
            'Experimental without using "--enable-experimental-features" '
            f"flag. {e}",
            file=sys.stderr,
        )
        exit(1)
    except merge_data.BadMappingFileError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def merge_get_marc_data_command(args: argparse.Namespace):
    with manage_module_logs(
        merge_data.logger, verbosity=get_logger_level_from_args(args)
    ):
        match args.from_getmarc_data_command:
            case "init-mapper":
                merge_data.generate_mapping_file_for_tsv(
                    args.source_tsv_file, args.output_file
                )
            case "merge":
                merge_from_getmarc(
                    metadata_tsv_file=args.metadata_tsv_file,
                    output_tsv_file=args.output_tsv_file,
                    mapping_file=args.mapping_file,
                    getmarc_server=args.getmarc_server,
                    enable_experimental_features=(
                        args.enable_experimental_features
                    ),
                )
            case _:
                raise ValueError(
                    f"unknown command: {args.from_getmarc_data_command}"
                )


def config_command(args: argparse.Namespace) -> None:
    match args.config_command:
        case "set":
            config = galatea.config.get_config()
            if args.key not in config.__dict__:
                raise ValueError(f"Unknown config key: {args.key}")
            setattr(config, args.key, args.value)
            galatea.config.set_config(config)

        case "show":
            config = galatea.config.get_config()
            for k, v in dataclasses.asdict(config).items():
                print(f"{k}: {v}")

        case _:
            raise ValueError(f"Unknown config command: {args.config_command}")


def verify_config_file(args: argparse.Namespace) -> None:
    if args.config_file.exists():
        logger.debug("Found existing config file: %s", args.config_file)
        return

    print(f"Creating new config file: {args.config_file}")
    if not args.config_file.parent.exists():
        args.config_file.parent.mkdir(parents=True)

    with args.config_file.open("w") as config_file:
        config_format = galatea.config.get_format_strategy()
        config_file.write(config_format.serialize(galatea.config.Config()))


startup_tasks: List[Callable[[argparse.Namespace], None]] = [
    verify_config_file
]


def main(cli_args: Optional[List[str]] = None) -> None:
    """Run main entry point."""
    arg_parser = get_arg_parser()
    argcomplete.autocomplete(arg_parser)
    args = arg_parser.parse_args(cli_args or sys.argv[1:])
    for task in startup_tasks:
        task(args)
    match args.command:
        case "clean-tsv":
            clean_tsv_command(args)

        case "authorized-terms":
            authorized_terms_command(args)

        case "merge-data":
            merge_data_command(args)

        case "authority-check":
            authority_check_command(args)
            deprecation_notice = "\n".join([
                "*" * 80,
                "DEPRECATION NOTICE: The subcommand `authority-check` is "
                "deprecated. Use `authorized-terms check` instead of "
                "`authority-check`",
                "*" * 80,
            ])
            logger.warning(deprecation_notice)

        case "config":
            config_command(args)


if __name__ == "__main__":
    main()
