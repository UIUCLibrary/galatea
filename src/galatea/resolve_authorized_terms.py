"""Resolving authorized terms."""

from __future__ import annotations

import collections.abc
import csv
import functools
import logging
import pathlib
import copy
from typing import (
    Optional,
    TypedDict,
    Iterable,
    TextIO,
    Callable,
    Collection,
    List,
    Tuple,
    Iterator,
    Dict,
    Union,
    Type,
)


import galatea.tsv
import galatea.marc
import difflib

__all__ = ["DEFAULT_TRANSFORMATION_FILE_NAME", "resolve_authorized_terms"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


TransformationData = TypedDict(
    "TransformationData",
    {
        "unauthorized term": str,
        "resolving authorized term": str,
    },
)

DEFAULT_TRANSFORMATION_FILE_NAME = "authorized_terms_transformation.tsv"
DEFAULT_TRANSFORMATION_FILE_CONTENT = (
    "unauthorized term\tresolving authorized term\n"
)


class Transform(collections.abc.Mapping[str, TransformationData]):
    dialect = "excel-tab"

    def __init__(self, fp: TextIO) -> None:
        self._fp = fp

    @classmethod
    @functools.cache
    def locate_in_file(
        cls, fp: TextIO, key: str
    ) -> Optional[TransformationData]:
        rows: Iterable[galatea.tsv.TableRow[TransformationData]] = (
            galatea.tsv.iter_tsv_fp(fp, dialect=cls.dialect)
        )
        for row in rows:
            if row.entry["unauthorized term"] == key:
                return row.entry
        return None

    def __getitem__(self, key: str) -> TransformationData:
        value = self.locate_in_file(self._fp, key)
        if value is None:
            raise KeyError(key)
        return value

    def transform(self, key: str) -> str:
        """Transform the key using the transformation file."""
        if key not in self:
            return key
        return self[key]["resolving authorized term"]

    def __len__(self) -> int:
        rows = 0
        for _ in galatea.tsv.iter_tsv_fp(self._fp, dialect=self.dialect):
            rows += 1
        return rows

    def __iter__(self) -> Iterator[str]:
        """Iterate over the entries in the transformation file."""
        row: galatea.tsv.TableRow[TransformationData]
        for row in galatea.tsv.iter_tsv_fp(self._fp, dialect=self.dialect):
            data: TransformationData = row.entry
            yield data["unauthorized term"]


default_resolved_fields = {"260$a", "264$a"}


def transform_authorized_terms(values: str, transformer: Transform) -> str:
    new_values: List[str] = []
    for value in values.split("||"):
        if transformation := transformer.transform(value.strip()):
            new_values.append(transformation.strip())
        else:
            new_values.append(value)

    return "||".join(new_values)


def iter_resolved_terms(
    table_rows: Iterable[galatea.tsv.TableRow[galatea.marc.Marc_Entry]],
    transformer: Transform,
    fields_to_resolve: Collection[str],
) -> Iterator[
    Tuple[
        galatea.tsv.TableRow[galatea.marc.Marc_Entry],
        galatea.tsv.TableRow[galatea.marc.Marc_Entry],
    ]
]:
    for row in table_rows:
        new_row = copy.deepcopy(row)
        for field in fields_to_resolve:
            if values := row.entry[field]:
                new_row.entry[field] = transform_authorized_terms(
                    values, transformer
                )
        yield row, new_row


def create_row_diff_report(
    original_row: galatea.tsv.TableRow[galatea.marc.Marc_Entry],
    new_row: galatea.tsv.TableRow[galatea.marc.Marc_Entry],
) -> str:
    elements: List[str] = []
    diff = diff_rows(original_row.entry, new_row.entry)
    for key, change in diff.items():
        differ = difflib.Differ()
        og_data, new_data = change
        delta = "\n".join(differ.compare([og_data or ""], [new_data or ""]))
        elements.append(
            f"  Line: {original_row.line_number}. Key: {key} :\n{delta}"
        )
        elements.append("_" * 80)

    return "\n".join(elements)


def diff_rows(
    row_a: galatea.marc.Marc_Entry, row_b: galatea.marc.Marc_Entry
) -> Dict[str, Tuple[Union[str, None], Union[str, None]]]:
    """Compare two rows and return the differences."""
    diff = {}
    for key in row_a.keys():
        if row_a[key] != row_b[key]:
            diff[key] = (row_a[key], row_b[key])
    return diff


ResolveStrategyCallback = Callable[
    [
        Iterable[galatea.tsv.TableRow[galatea.marc.Marc_Entry]],
        Transform,
        Collection[str],
    ],
    Iterable[
        Tuple[
            galatea.tsv.TableRow[galatea.marc.Marc_Entry],
            galatea.tsv.TableRow[galatea.marc.Marc_Entry],
        ]
    ],
]
"""Callback function to resolve unauthorized terms to authorized terms."""


def resolve_authorized_terms(
    input_tsv: pathlib.Path,
    transformation_file: pathlib.Path,
    output_file: pathlib.Path,
    input_tsv_dialect: Optional[Union[Type[csv.Dialect], csv.Dialect]] = None,
    resolve_strategy: ResolveStrategyCallback = iter_resolved_terms,
) -> None:
    """Resolve unauthorized terms to authorized terms in found tsv file.

    Args:
        input_tsv_dialect: The dialect of the input tsv file. If None, it will
            attempt to guess
        input_tsv: The input tsv file to be transformed.
        transformation_file: The file to define transformations.
        output_file: Output file name.
        resolve_strategy: Callable that returns a tuple of the original and new
            row.

    """
    # Opening the output file and the input are not done at the same time so
    # that a user can write the modified data to the same file as the input.

    with transformation_file.open("r", encoding="utf-8") as fp:
        transformer = Transform(fp)
        new_data: List[galatea.marc.Marc_Entry] = []

        if input_tsv_dialect is None:
            with input_tsv.open("r", encoding="utf-8") as input_tsv_fp:
                input_tsv_dialect = galatea.tsv.get_tsv_dialect(input_tsv_fp)

        for original_row, new_row in resolve_strategy(
            galatea.tsv.iter_tsv_file(input_tsv, dialect=input_tsv_dialect),
            transformer,
            default_resolved_fields,
        ):
            new_data.append(new_row.entry)
            if original_row.entry != new_row.entry:
                logger.log(
                    galatea.VERBOSE_LEVEL_NUM,
                    msg=create_row_diff_report(
                        original_row=original_row, new_row=new_row
                    ),
                )
    with output_file.open("w", encoding="utf-8") as fp:
        galatea.tsv.write_tsv_fp(fp, data=new_data, dialect=input_tsv_dialect)
    logger.info(f"Wrote to {output_file.name}")


def create_init_transformation_file_fp(fp: TextIO) -> None:
    """Create a new transformation file with the header."""
    logger.debug("creating new transformation tsv file")
    if fp.closed:
        raise ValueError("File pointer is closed")
    fp.write(DEFAULT_TRANSFORMATION_FILE_CONTENT)


def create_init_transformation_file(
    output: pathlib.Path,
    write_strategy: Callable[
        [TextIO], None
    ] = create_init_transformation_file_fp,
) -> None:
    """Create a new transformation file with the header."""
    logger.debug("creating new transformation tsv file")
    if output.exists():
        raise FileExistsError(output.absolute())
    with output.open("w", encoding="utf-8") as fp:
        write_strategy(fp)
    logger.info(f"Wrote new transformation tsv file to {output.absolute()}")
    return None
