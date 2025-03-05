from unittest.mock import Mock, patch, mock_open

import pytest
import requests

from galatea import validate_authorized_terms

class TestCachedApiCheck:
    def test_adds_to_cache(self):
        cached_api = validate_authorized_terms.CachedApiCheck(
            requesting_strategy=Mock())
        assert len(cached_api.data_cache) == 0
        cached_api.get_data("https://example.com/api/spam")
        assert len(cached_api.data_cache) == 1

    def test_reuse_cached_value(self):
        response = Mock(spec_set=requests.Request)

        requesting_strategy = Mock(
            name="requesting_strategy",
            return_value=response
        )
        cached_api = validate_authorized_terms.CachedApiCheck(
            requesting_strategy=requesting_strategy)
        assert cached_api.get_data("https://example.com/api/spam") == response
        assert cached_api.get_data("https://example.com/api/spam") == response
        requesting_strategy.assert_called_once()

    def test_clear_cache(self):
        requesting_strategy = Mock(name="requesting_strategy")
        cached_api = validate_authorized_terms.CachedApiCheck(
            requesting_strategy=requesting_strategy)
        cached_api.get_data("https://example.com/api/spam")
        cached_api.clear_cache()
        cached_api.get_data("https://example.com/api/spam")
        assert requesting_strategy.call_count == 2

    def test_contains(self):
        requesting_strategy = Mock(name="requesting_strategy")
        cached_api = \
            validate_authorized_terms.CachedApiCheck(
                requesting_strategy=requesting_strategy
            )
        cached_api.get_data("https://example.com/api/spam")
        assert "https://example.com/api/spam" in cached_api

class TestNameCheck:
    def test_contains(self):
        response = Mock(spec_set=requests.Request)
        requesting_strategy = Mock(
            name="requesting_strategy",
            return_value=response
        )
        check = validate_authorized_terms.NameCheck(requesting_strategy)
        check.get_data("spam")
        assert "spam" in check

    def test_contains_non_string(self):
        check = validate_authorized_terms.NameCheck()
        assert (1,2) not in check

    def test_get_data_includes_url(self):
        response = Mock(spec_set=requests.Request)
        requesting_strategy = Mock(
            name="requesting_strategy",
            return_value=response
        )
        check = validate_authorized_terms.NameCheck(requesting_strategy)
        check.get_data("spam")
        requesting_strategy.assert_called_once_with(
            "https://id.loc.gov/authorities/names/label/spam"
        )

@pytest.mark.parametrize(
    "status_code, expected", [
        (200, True),
        (404, False),
    ]
)
def test_check_name(status_code, expected):
    response = Mock(spec=requests.Response, status_code=status_code)
    cache = Mock(
        spec_set=validate_authorized_terms.CachedApiCheck,
        get_data=Mock(return_value=response)
    )
    assert validate_authorized_terms.check_terms("spam", cache) is expected

def test_optional_rate_limited_callable_generator_passes_values():
    assert next(
        iter(
            validate_authorized_terms.optional_rate_limited_iterator(
                [(True, "a")],
                sleep_func=Mock()
            )
        )
    ) == (True, "a")

def test_optional_rate_limited_callable_generator_passes_calls_sleep():
    sleep_func = Mock()
    list(
        validate_authorized_terms.optional_rate_limited_iterator(
            [
                (True, "a"),
                (True, "b"),
            ],
            sleep_func=sleep_func
        )
    )
    sleep_func.assert_called_once()


def test_validate_authorized_terms(monkeypatch):
    monkeypatch.setattr(
        validate_authorized_terms.IterTerms,
        "__iter__",
        Mock(return_value=iter([
            (1, "abc", "efh")
        ]))
    )
    check_terms = Mock(name="check_terms")

    monkeypatch.setattr(
        validate_authorized_terms, "check_terms", check_terms
    )
    validate_authorized_terms.validate_authorized_terms("spam")
    check_terms.assert_called_once()

def test_validate_authorized_terms_logs_if_return_false(
        monkeypatch, caplog):
    monkeypatch.setattr(
        validate_authorized_terms.IterTerms,
        "__iter__",
        Mock(return_value=iter([
            (1, "abc", "efh")
        ]))
    )
    check_terms = Mock(name="check_terms", return_value=False)

    monkeypatch.setattr(
        validate_authorized_terms, "check_terms", check_terms
    )

    validate_authorized_terms.validate_authorized_terms("spam")
    assert "is not an authorized term" in caplog.text


class TestIterTerms:
    def test_iter(self):
        term_interator = validate_authorized_terms.IterTerms("spam.tsv")
        term_interator.iter_rows = Mock(return_value=iter([
            Mock(
                line_number=1,
                entry={
                    '264$a': "one",
                    '264$b': "two",
                    '264$c': None
                }
            )
        ]))
        term_interator.field_names.add("264$a")
        term_interator.field_names.add("264$c")
        assert list(term_interator) == [(1, '264$a', "one")]

    def test_iter_rows(self):
        term_interator = validate_authorized_terms.IterTerms("spam.tsv")
        validate_authorized_terms.IterTerms.tsv_file_row_iterator = Mock(
            return_value=[
                {'264$a': "one", '264$b': "two"}
            ]
        )
        with patch("galatea.validate_authorized_terms.open", mock_open(read_data="")):
            assert list(term_interator.iter_rows()) == [
                {'264$a': "one", '264$b': "two"}
            ]
