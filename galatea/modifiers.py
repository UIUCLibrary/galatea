"""Modifying functions for string data."""

from __future__ import annotations

import functools
import re
import typing
from typing import List, Callable, Optional
from importlib.resources import files
from functools import reduce

if typing.TYPE_CHECKING:
    from galatea.marc import MarcEntryDataTypes

def split_and_modify(
    entry: MarcEntryDataTypes,
    funcs: List[Callable[[MarcEntryDataTypes], MarcEntryDataTypes]],
    delimiter: str = "||",
) -> MarcEntryDataTypes:
    """Split the entry into and apply function to each element."""
    if entry is None:
        return None
    values = entry.split(delimiter)
    new_values: List[str] = []
    for value in values:
        if value is not None:
            new_values.append(
                reduce(
                    lambda result, func: typing.cast(
                        Callable[[str], str], func
                    )(result),
                    funcs,
                    value,
                )
            )
    return delimiter.join(new_values)


def remove_duplicates(
    entry: MarcEntryDataTypes, delimiter: str = "||"
) -> MarcEntryDataTypes:
    """Remove duplicate items and retains order.

    Args:
        entry: value to remove duplicates.
        delimiter: character used to separate the items in the string

    Returns: new text with duplicates removed.

    """
    if entry is None:
        return None
    values = entry.split(delimiter)
    new_values: List[str] = []
    for value in values:
        if value in new_values:
            continue
        new_values.append(value)

    return delimiter.join(new_values)


def remove_trailing_periods(entry: MarcEntryDataTypes) -> MarcEntryDataTypes:
    """Remove trailing period."""
    if entry is None:
        return None
    if entry.endswith("."):
        return entry[:-1]
    return entry


def remove_double_dash_postfix(
    entry: MarcEntryDataTypes,
) -> MarcEntryDataTypes:
    """Remove double dash postfix."""
    if entry is None:
        return None
    match = re.search("--[a-z]+", entry)
    if match:
        return entry[: match.start()]
    return entry


def add_comma_after_space(entry: MarcEntryDataTypes) -> MarcEntryDataTypes:
    """Add comma after space."""
    if entry is None:
        return None
    return entry.replace(",", ", ").replace(",  ", ", ")


def remove_character(
    entry: MarcEntryDataTypes, character: str
) -> MarcEntryDataTypes:
    """Remove character from text."""
    if entry is None:
        return None
    return entry.replace(character, "")


DEFAULT_PUNCTUATION_TO_REMOVE = [".", ",", ";", ":"]


def remove_trailing_punctuation(
    entry: MarcEntryDataTypes, punctuation: Optional[List[str]] = None
) -> MarcEntryDataTypes:
    """Remove trailing punctuation."""
    if entry is None:
        return None
    return entry.rstrip("".join(punctuation or DEFAULT_PUNCTUATION_TO_REMOVE))


def regex_transform(
    entry: MarcEntryDataTypes, pattern: str, replacement: str
) -> MarcEntryDataTypes:
    """Apply regular expression to entry."""
    if entry is None:
        return None
    return re.sub(pattern, replacement, entry)

@functools.cache
def _get_relator_term_regex():
    terms = (
        files("galatea").joinpath('relator_terms.txt').read_text().split("\n")
    )
    relator_terms_in_regex = "|".join(terms)
    return fr"({relator_terms_in_regex})\.?"

def remove_relator_terms(entry: MarcEntryDataTypes):
    """Remove any relator terms from the string.

    See https://www.loc.gov/marc/relators/relaterm.html

    Args:
        entry: single element value from a mark file

    Returns:
        entry with relator terms removed

    """
    if entry is None:
        return None
    return re.sub(_get_relator_term_regex(), "", entry)
