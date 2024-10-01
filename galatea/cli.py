"""cli interface to galatea."""

import argparse
import pathlib
from importlib import metadata
from typing import Optional
from galatea import clean_tsv


def get_versions_from_package() -> Optional[str]:
    """Get version information from the package metadata."""
    try:
        return metadata.version(__package__)
    except metadata.PackageNotFoundError:
        return None


DEFAULT_VERSION_STRATEGIES = [
    get_versions_from_package
]


def get_version() -> str:
    """Get the version of current application."""

    for strategy in DEFAULT_VERSION_STRATEGIES:
        version = strategy()
        if version:
            return version
    return "unknown version"


def get_arg_parser() -> argparse.ArgumentParser:
    """Argument parser for galatea cli."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {get_version()}'
    )

    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        description='valid commands'
    )

    clean_tsv_cmd = subparsers.add_parser('clean-tsv', help='clean TSV files')

    clean_tsv_cmd.add_argument(
        "source_tsv",
        type=pathlib.Path,
        help="Source tsv file"
    )

    clean_tsv_cmd.add_argument(
        "output_tsv",
        type=pathlib.Path,
        help="Output tsv file"
    )
    return parser


def main() -> None:
    """Main entry point."""
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    match(args.command):
        case "clean-tsv":
            clean_tsv.clean_tsv(args.source_tsv, args.output_tsv)


if __name__ == '__main__':
    main()
