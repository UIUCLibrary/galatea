from galatea import modifiers

def test_remove_duplicates():
    assert modifiers.remove_duplicates('a||a||b') == "a||b"


def test_remove_trailing_periods():
    assert modifiers.remove_trailing_periods("spam.") == "spam"


def test_remove_double_dash_postfix():
    assert modifiers.remove_double_dash_postfix("spam--upper") == "spam"

