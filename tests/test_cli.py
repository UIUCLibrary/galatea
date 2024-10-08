import argparse
from unittest.mock import Mock, create_autospec

import pytest

import galatea.cli
import galatea.clean_tsv

def test_clean_tsv_command_called(monkeypatch):
    args = ["clean-tsv", "spam.tsv"]
    clean_tsv_command = Mock()
    monkeypatch.setattr(galatea.cli, "clean_tsv_command", clean_tsv_command)
    galatea.cli.main(args)
    clean_tsv_command.assert_called_once()

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
    clean_tsv.assert_called_once_with(source="spam.tsv", dest="bacon.tsv")


def test_clean_tsv_command_w_no_output_calls_clean_tsv_inplace(monkeypatch):
    clean_tsv = create_autospec(galatea.clean_tsv.clean_tsv)
    monkeypatch.setattr(galatea.clean_tsv, "clean_tsv", clean_tsv)
    galatea.cli.clean_tsv_command(
        argparse.Namespace(
            source_tsv="spam.tsv",
            output_tsv=None,
        ),
    )
    clean_tsv.assert_called_once_with(source="spam.tsv", dest="spam.tsv")

def test_no_sub_command_returns_non_zero():
    with pytest.raises(SystemExit) as e:
        galatea.cli.main([])
    assert e.value.code != 0
