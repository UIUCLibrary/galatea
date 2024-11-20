"""Cleaning tsv file subcommand."""

import csv
import contextlib
import logging
import pathlib
from collections.abc import Iterator
from typing import (
    Iterable,
    Dict,
    List,
    Callable,
    TextIO,
    Union,
    Protocol,
    Type,
    Optional,
)
from functools import reduce
from galatea import modifiers

__all__ = ["clean_tsv"]


_Marc_Entry = Dict[str, Union[str, None]]

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def remembered_file_pointer_head(fp: TextIO) -> Iterator[TextIO]:
    starting = fp.tell()
    try:
        yield fp
    finally:
        fp.seek(starting)


def iter_tsv_fp(
    fp: TextIO, dialect: Union[Type[csv.Dialect], csv.Dialect]
) -> Iterable[_Marc_Entry]:
    with remembered_file_pointer_head(fp):
        yield from csv.DictReader(fp, dialect=dialect)


def iter_tsv_file(
    file_name: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    strategy: Callable[
        [TextIO, Union[Type[csv.Dialect], csv.Dialect]], Iterable[_Marc_Entry]
    ] = iter_tsv_fp,
) -> Iterable[_Marc_Entry]:
    with open(file_name, newline="", encoding="utf8") as tsv_file:
        yield from strategy(tsv_file, dialect)


def apply_filters(filter_funcs: List[Callable[[str], str]], entry: str) -> str:
    return reduce(lambda result, func: func(result), filter_funcs, entry)


def row_modifier(row: _Marc_Entry) -> _Marc_Entry:
    def modify(_: str, value: Optional[str]) -> Optional[str]:
        def modify(entry: str) -> str:
            functions = [
                modifiers.remove_double_dash_postfix,
                modifiers.remove_trailing_periods,
                modifiers.add_comma_after_space
            ]
            return reduce(lambda result, func: func(result), functions, entry)
        return (
            apply_filters(
                entry=value,
                filter_funcs=[
                    lambda entry: modifiers.split_and_modify(
                        entry, func=modify
                    ),
                    modifiers.remove_duplicates,
                ],
            )
            if value is not None
            else None
        )

    modified_entries = {k: modify(k, v) for k, v in row.items()}
    return modified_entries


def write_tsv_fp(
    fp: TextIO,
    data: List[_Marc_Entry],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
) -> None:
    try:
        fieldnames = data[0].keys()
    except IndexError:
        logger.warning("No tsv data written.")
        return
    writer = csv.DictWriter(fp, fieldnames=fieldnames, dialect=dialect)
    writer.writeheader()
    for row in data:
        writer.writerow(row)


def write_tsv_file(
    file_name: pathlib.Path,
    data: List[_Marc_Entry],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    writing_strategy: Callable[
        [TextIO, List[_Marc_Entry], Union[Type[csv.Dialect], csv.Dialect]],
        None,
    ] = write_tsv_fp,
) -> None:
    with open(file_name, "w", newline="", encoding="utf8") as tsv_file:
        writing_strategy(tsv_file, data, dialect)


class UnknownDialect(Exception):
    """Unable to detect tsv dialect."""


class DetectionStrategy(Protocol):
    def __call__(self, fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
        """Detect the dialect of a tsv file.

        if unable to figure it out, the function throws a DialectDetectionError
        """


def _sniff_tsv_dialect(fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
    with remembered_file_pointer_head(fp):
        try:
            sniffer = csv.Sniffer()
            return sniffer.sniff(fp.read(1024 * 2), delimiters="\t")
        except csv.Error as e:
            raise UnknownDialect() from e


def get_tsv_dialect(
    fp: TextIO, detection_strategy: DetectionStrategy = _sniff_tsv_dialect
) -> Union[Type[csv.Dialect], csv.Dialect]:
    with remembered_file_pointer_head(fp):
        try:
            return detection_strategy(fp)
        except UnknownDialect as e:
            logger.warning(
                'Using "excel-tab" for tsv dialect due to unknown tsv '
                "dialect. Reason: %s",
                e,
            )
            return csv.get_dialect("excel-tab")


def make_empty_strings_none(record: _Marc_Entry) -> _Marc_Entry:
    new_record = record.copy()
    for key, value in record.items():
        if not value:
            new_record[key] = None
        else:
            new_record[key] = value
    return new_record


def transform_row_and_merge(
    row: _Marc_Entry,
    row_transformation_strategy: Callable[[_Marc_Entry], _Marc_Entry],
) -> _Marc_Entry:
    modifications = row_transformation_strategy(row)
    merged: _Marc_Entry = {**row, **modifications}
    merged = make_empty_strings_none(merged)
    return merged


def clean_tsv(source: pathlib.Path, dest: pathlib.Path) -> None:
    """Clean tsv file.

    Args:
        source: source tsv file
        dest: output file name

    """
    with open(source, newline="", encoding="utf-8") as tsv_file:
        dialect = get_tsv_dialect(tsv_file)

        modified_data = [
            transform_row_and_merge(
                row, row_transformation_strategy=row_modifier
            )
            for row in iter_tsv_fp(tsv_file, dialect)
        ]

    write_tsv_file(dest, modified_data, dialect)
    print(f'Done. Wrote to "{dest.absolute()}"')
