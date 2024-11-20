"""Cleaning tsv file subcommand."""

import logging
import pathlib
import typing
from typing import Dict, List, Callable, Union, Optional, Iterable
from functools import reduce
from galatea import modifiers, data_file

__all__ = ["clean_tsv"]

_Marc_Entry = Dict[str, Union[str, None]]

logger = logging.getLogger(__name__)


def apply_filters(filter_funcs: List[Callable[[str], str]], entry: str) -> str:
    return reduce(lambda result, func: func(result), filter_funcs, entry)


def row_modifier(row: _Marc_Entry) -> _Marc_Entry:
    def modify(_: str, value: Optional[str]) -> Optional[str]:
        def modify(entry: str) -> str:
            functions = [
                modifiers.remove_double_dash_postfix,
                modifiers.remove_trailing_periods,
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
        dialect = data_file.get_tsv_dialect(tsv_file)

        modified_data: List[_Marc_Entry] = [
            transform_row_and_merge(
                row, row_transformation_strategy=row_modifier
            )
            for row in typing.cast(
                Iterable[_Marc_Entry], data_file.iter_tsv_fp(tsv_file, dialect)
            )
        ]

    data_file.write_tsv_file(dest, modified_data, dialect)
    print(f'Done. Wrote to "{dest.absolute()}"')
