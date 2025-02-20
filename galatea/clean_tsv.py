"""Cleaning tsv file subcommand."""

import csv
import contextlib
import functools
import logging
import pathlib
from collections.abc import Iterator
from typing import (
    Iterable,
    List,
    Callable,
    TextIO,
    Union,
    Protocol,
    Type,
    Optional,
    Tuple,
)
from galatea import modifiers

__all__ = ["clean_tsv"]

from galatea.marc import MarcEntryDataTypes, Marc_Entry

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
) -> Iterable[Marc_Entry]:
    with remembered_file_pointer_head(fp):
        yield from csv.DictReader(fp, dialect=dialect)


def iter_tsv_file(
    file_name: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    strategy: Callable[
        [TextIO, Union[Type[csv.Dialect], csv.Dialect]], Iterable[Marc_Entry]
    ] = iter_tsv_fp,
) -> Iterable[Marc_Entry]:
    with open(file_name, newline="", encoding="utf8") as tsv_file:
        yield from strategy(tsv_file, dialect)


class RowTransformer:
    def __init__(self) -> None:
        self.transformations: List[
            Tuple[
                Callable[[MarcEntryDataTypes], Union[MarcEntryDataTypes]],
                Optional[Callable[[str, MarcEntryDataTypes], bool]],
            ]
        ] = []

    def transform(self, row: Marc_Entry) -> Marc_Entry:
        new_row = row.copy()
        for k, v in row.items():
            for transformation, condition in self.transformations:
                if condition is None or condition(k, v) is True:
                    transformed_value = transformation(new_row[k])
                    new_row[k] = transformed_value
        return new_row

    def add_transformation(
        self,
        transformation: Callable[
            [MarcEntryDataTypes], Union[MarcEntryDataTypes]
        ],
        condition: Optional[Callable[[str, MarcEntryDataTypes], bool]] = None,
    ) -> None:
        self.transformations.append((transformation, condition))


def default_row_modifier() -> RowTransformer:
    transformer = RowTransformer()

    transformer.add_transformation(
        transformation=lambda entry: modifiers.split_and_modify(
            entry,
            funcs=[
                modifiers.remove_double_dash_postfix,
                modifiers.remove_trailing_periods,
                modifiers.add_comma_after_space,
            ],
        )
    )

    transformer.add_transformation(
        condition=lambda k, v: k
        in ["260$a","260$b", "260$c", "264$a", "264$b", "264$c"],
        transformation=lambda entry: modifiers.split_and_modify(
            entry,
            funcs=[
                functools.partial(modifiers.remove_character, character="?"),
                functools.partial(modifiers.remove_character, character="["),
                functools.partial(modifiers.remove_character, character="]"),
                modifiers.remove_trailing_punctuation,
            ],
        ),
    )

    transformer.add_transformation(
        condition=lambda k, v: k in ["300$ab", "300$c"],
        transformation=lambda entry: modifiers.split_and_modify(
            entry,
            funcs=[
                modifiers.remove_trailing_punctuation,
                functools.partial(modifiers.remove_trailing_punctuation, punctuation=[" "]),
                modifiers.remove_trailing_punctuation,
            ],
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "610",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(--)(?=[A-Z])",
            replacement=" "
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "710",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(--)(?=[A-Z])",
            replacement=" "
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "710",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(?<=[a-z])([.])(?=[A-Z])",
            replacement=". "
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k in ["650",
                                     "651",
                                     "655",
                                     "600",
                                     "610",
                                     "611",
                                     "700",
                                     "710",
                                     "711"],
        transformation=functools.partial(
            modifiers.remove_trailing_punctuation,
            punctuation=["."]
        )
    )
    transformer.add_transformation(modifiers.remove_duplicates)
    return transformer


def row_modifier(
    row: Marc_Entry, transformer: Optional[RowTransformer] = None
) -> Marc_Entry:
    transformer = transformer or default_row_modifier()
    return transformer.transform(row)


def write_tsv_fp(
    fp: TextIO,
    data: List[Marc_Entry],
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
    data: List[Marc_Entry],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    writing_strategy: Callable[
        [TextIO, List[Marc_Entry], Union[Type[csv.Dialect], csv.Dialect]],
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


def make_empty_strings_none(record: Marc_Entry) -> Marc_Entry:
    new_record = record.copy()
    for key, value in record.items():
        if not value:
            new_record[key] = None
        else:
            new_record[key] = value
    return new_record


def transform_row_and_merge(
    row: Marc_Entry,
    row_transformation_strategy: Callable[[Marc_Entry], Marc_Entry],
) -> Marc_Entry:
    modifications = row_transformation_strategy(row)
    merged: Marc_Entry = {**row, **modifications}
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
                row,
                row_transformation_strategy=functools.partial(
                    row_modifier, transformer=default_row_modifier()
                ),
            )
            for row in iter_tsv_fp(tsv_file, dialect)
        ]

    write_tsv_file(dest, modified_data, dialect)
    print(f'Done. Wrote to "{dest.absolute()}"')
