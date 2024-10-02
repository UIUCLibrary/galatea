import pytest

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
        "spam.||bacon.", modifiers.remove_trailing_periods
    ) == "spam||bacon"
