"""Modifying functions for string data."""
import re
from typing import List, Callable


def split_and_modify(
    entry: str, func: Callable[[str], str], delimiter: str = "||"
) -> str:
    """Split the entry into and apply function to each element."""
    values = entry.split(delimiter)
    new_values: List[str] = []
    for value in values:
        new_values.append(func(value))
    return delimiter.join(new_values)


def remove_duplicates(entry: str, delimiter: str = "||") -> str:
    """Remove duplicate items and retains order.

    Args:
        entry: value to remove duplicates.
        delimiter: character used to separate the items in the string

    Returns: new text with duplicates removed.

    """
    values = entry.split(delimiter)
    new_values: List[str] = []
    for value in values:
        if value in new_values:
            continue
        new_values.append(value)

    return delimiter.join(new_values)


def remove_trailing_periods(entry: str) -> str:
    """Remove trailing period."""
    if entry.endswith("."):
        return entry[:-1]
    return entry


def remove_double_dash_postfix(entry: str) -> str:
    """Remove double dash postfix."""
    match = re.search("--[a-z]+", entry)
    if match:
        return entry[:match.start()]
    return entry
