"""Cleaning tsv file subcommand."""
import pathlib


def clean_tsv(source: pathlib.Path, dest: pathlib.Path) -> None:
    """Clean tsv file.

    Args:
        source: source tsv file
        dest: output file name

    """
    with open(source, "r", encoding="utf-8") as source_tsv:
        dest.write_text(source_tsv.read())
    print(f'Read file "{source}" and saved a cleaned version as "{dest}"')
