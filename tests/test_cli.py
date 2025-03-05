import argparse
import logging
from unittest.mock import Mock, create_autospec, ANY

import pytest

import galatea.cli
import galatea.clean_tsv


@pytest.mark.parametrize(
    "args, function_name",
    [
        (["authority-check", "spam.tsv"], "authority_check_command"),
        (["clean-tsv", "spam.tsv"], "clean_tsv_command"),
    ],
)
def test_command_called(monkeypatch, args, function_name):
    command = Mock()
    monkeypatch.setattr(galatea.cli, function_name, command)
    galatea.cli.main(args)
    command.assert_called_once()


def test_clean_tsv_fails_with_no_args():
    args = ["clean-tsv"]
    with pytest.raises(SystemExit):
        galatea.cli.main(args)


def test_clean_tsv_command_calls_clean_tsv(monkeypatch):
    clean_tsv = create_autospec(galatea.clean_tsv.clean_tsv)
    monkeypatch.setattr(galatea.clean_tsv, "clean_tsv", clean_tsv)
    galatea.cli.clean_tsv_command(
        argparse.Namespace(
            source_tsv="spam.tsv",
            output_tsv="bacon.tsv",
        ),
    )
    clean_tsv.assert_called_once_with(
        source="spam.tsv", dest="bacon.tsv", row_diff_report_generator=ANY
    )


def test_clean_tsv_command_w_no_output_calls_clean_tsv_inplace(monkeypatch):
    clean_tsv = create_autospec(galatea.clean_tsv.clean_tsv)
    monkeypatch.setattr(galatea.clean_tsv, "clean_tsv", clean_tsv)
    galatea.cli.clean_tsv_command(
        argparse.Namespace(
            source_tsv="spam.tsv",
            output_tsv=None,
        ),
    )
    clean_tsv.assert_called_once_with(
        source="spam.tsv", dest="spam.tsv", row_diff_report_generator=ANY
    )


def test_no_sub_command_returns_non_zero():
    with pytest.raises(SystemExit) as e:
        galatea.cli.main([])
    assert e.value.code != 0


@pytest.mark.parametrize(
    "input_verbose_level, expected_level_level",
    [
        (0, logging.INFO),
        (1, galatea.VERBOSE_LEVEL_NUM),
        (2, logging.DEBUG),
    ],
)
def test_get_logger_level_from_args(input_verbose_level, expected_level_level):
    args = argparse.Namespace(verbosity=input_verbose_level)
    assert galatea.cli.get_logger_level_from_args(args) == expected_level_level


def test_get_logger_level_defaults_to_into():
    # Note that the args do not include "verbosity"
    assert (
        galatea.cli.get_logger_level_from_args(argparse.Namespace())
        == logging.INFO
    )


def test_authority_check_command(monkeypatch):
    args = argparse.Namespace(source_tsv="dummy.tsv")
    validate_authorized_terms = Mock(name="validate_authorized_terms")
    monkeypatch.setattr(
        galatea.validate_authorized_terms,
        "validate_authorized_terms",
        validate_authorized_terms,
    )
    galatea.cli.authority_check_command(args)
    validate_authorized_terms.assert_called_once_with("dummy.tsv")
