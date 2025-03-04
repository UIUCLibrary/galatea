"""Cleaning tsv file subcommand."""

import functools
import logging
import pathlib
import difflib
from typing import (
    List,
    Callable,
    Union,
    Optional,
    Tuple,
    TypeVar,
)
import galatea
from galatea import modifiers
from galatea.marc import MarcEntryDataTypes, Marc_Entry
from galatea.tsv import (
    TableRow,
    write_tsv_file,
    get_tsv_dialect,
    iter_tsv_fp
)

__all__ = ["clean_tsv"]

T = TypeVar("T")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        in ["260$a", "260$b", "260$c", "264$a", "264$b", "264$c"],
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
                functools.partial(
                    modifiers.remove_trailing_punctuation, punctuation=[" "]
                ),
                modifiers.remove_trailing_punctuation,
            ],
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "610",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(--)(?=[A-Z])",
            replacement=" ",
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "710",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(--)(?=[A-Z])",
            replacement=" ",
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k == "710",
        transformation=functools.partial(
            modifiers.regex_transform,
            pattern=r"(?<=[a-z])([.])(?=[A-Z])",
            replacement=". ",
        ),
    )

    transformer.add_transformation(
        condition=lambda k, _: k
        in ["650", "651", "655", "600", "610", "611", "700", "710", "711"],
        transformation=functools.partial(
            modifiers.remove_trailing_punctuation, punctuation=["."]
        ),
    )
    transformer.add_transformation(modifiers.remove_duplicates)
    return transformer


def row_modifier(
    row: Marc_Entry, transformer: Optional[RowTransformer] = None
) -> Marc_Entry:
    transformer = transformer or default_row_modifier()
    return transformer.transform(row)


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


def clean_tsv(
    source: pathlib.Path,
    dest: pathlib.Path,
    row_diff_report_generator: Optional[
        Callable[[TableRow[Marc_Entry], TableRow[Marc_Entry], List[str]], str]
    ] = None,
) -> None:
    """Clean tsv file.

    Args:
        source: source tsv file
        dest: output file name
        row_diff_report_generator: function for generating reports explaining
            the changes in the row

    """
    logger.debug("Reading %s", source)
    with open(source, newline="", encoding="utf-8") as tsv_file:
        modified_data = []
        dialect = get_tsv_dialect(tsv_file)
        field_names = galatea.tsv.get_field_names(source)
        for row in iter_tsv_fp(tsv_file, dialect):
            transformed_row = transform_row_and_merge(
                row.entry,
                row_transformation_strategy=functools.partial(
                    row_modifier, transformer=default_row_modifier()
                ),
            )
            if row_diff_report_generator is not None:
                if diff_report := row_diff_report_generator(
                    row,
                    TableRow(
                        line_number=row.line_number, entry=transformed_row
                    ),
                    field_names,
                ):
                    logger.log(galatea.VERBOSE_LEVEL_NUM, msg=diff_report)
            modified_data.append(transformed_row)

    write_tsv_file(dest, modified_data, dialect)
    logger.info(f'Modified tsv wrote to "{dest.absolute()}"')
    print("Done.")


def create_diff_report(
    unmodified_row: TableRow[Marc_Entry],
    transformed_row: TableRow[Marc_Entry],
    fieldnames: List[str],
):
    changed = {}
    for k in fieldnames:
        a: str = (unmodified_row.entry.get(k, "") or "").strip()
        b: str = (transformed_row.entry.get(k, "") or "").strip()
        if a == b:
            continue
        entry_differ = difflib.Differ()
        res = entry_differ.compare([a], [b])
        changed[k] = "\n".join(list(res))
    if len(changed) == 0:
        return None
    lines: List[str] = []
    for k, v in changed.items():
        lines.append("")
        lines.append(f"Row  : {unmodified_row.line_number}")
        lines.append(f"Field: {k}")
        lines.append("")
        lines.append("Changes:\n")
        lines.append(v)
        lines.append("=" * 80)
    return "\n".join(lines)
