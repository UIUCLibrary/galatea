import pytest

import functools
from galatea import modifiers

def test_remove_duplicates():
    assert modifiers.remove_duplicates('a||a||b') == "a||b"


def test_remove_trailing_periods():
    assert modifiers.remove_trailing_periods("spam.") == "spam"


def test_remove_trailing_periods_ignores_invalid():
    assert modifiers.remove_trailing_periods("spam") == "spam"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("spam", "spam"),
        ("spam--upper", "spam"),
        ("spam -- okay", "spam -- okay"),
    ]
)
def test_remove_double_dash_postfix(value, expected):
    assert modifiers.remove_double_dash_postfix(value) == expected

def test_split_and_modify():
    assert modifiers.split_and_modify(
        "spam.||bacon.", [modifiers.remove_trailing_periods]
    ) == "spam||bacon"

def test_add_space_after_comma():
    starting = "Persac, Marie Adrien,1823-1873"
    assert modifiers.add_comma_after_space(starting) == "Persac, Marie Adrien, 1823-1873"

def test_remove_character():
    starting = "Chicago, Ill.?"
    assert modifiers.remove_character(starting, "?") == "Chicago, Ill."


def test_remove_character_does_not_change_in_not_included():
    starting = "Chicago, Ill."
    assert modifiers.remove_character(starting, "?") == starting

@pytest.mark.parametrize(
    "filter_func",
    [
        functools.partial(modifiers.remove_character, character="?"),
        modifiers.add_comma_after_space,
        modifiers.remove_double_dash_postfix,
        modifiers.remove_duplicates,
        modifiers.remove_trailing_periods,
    ]
)
def test_none_returns_none(filter_func):
    assert filter_func(None) is None