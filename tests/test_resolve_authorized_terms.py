import io
import pathlib
from unittest.mock import Mock, MagicMock

import pytest

import galatea.tsv
from galatea import resolve_authorized_terms
from galatea.tsv import TableRow


class TestTransform:
    @pytest.fixture
    def sample_file_handle(self):
        return io.StringIO(
            """
unauthorized term\tresolving authorized term
spam.	Spam
""".strip()
        )

    def test_get_item(self, sample_file_handle):
        assert (
            resolve_authorized_terms.Transform(sample_file_handle)["spam."][
                "resolving authorized term"
            ]
            == "Spam"
        )

    def test_get_item_not_found(self, sample_file_handle):
        with pytest.raises(KeyError):
            assert resolve_authorized_terms.Transform(sample_file_handle)[
                "missing key"
            ]

    def test_len(self, sample_file_handle):
        assert len(resolve_authorized_terms.Transform(sample_file_handle)) == 1

    def test_iter(self, sample_file_handle):
        transformer = resolve_authorized_terms.Transform(sample_file_handle)
        assert next(iter(transformer)) == "spam."


def test_create_init_transformation_file_fp():
    fp = io.StringIO()
    resolve_authorized_terms.create_init_transformation_file_fp(fp)
    assert (
        fp.getvalue()
        == resolve_authorized_terms.DEFAULT_TRANSFORMATION_FILE_CONTENT
    )


def test_create_init_transformation_file_fp_with_fp_closed():
    fp = io.StringIO()
    fp.close()
    with pytest.raises(ValueError):
        resolve_authorized_terms.create_init_transformation_file_fp(fp)


def test_create_init_transformation_file():
    sample_output = MagicMock(spec_set=pathlib.Path, exists=lambda *_: False)
    write_strategy = Mock()
    resolve_authorized_terms.create_init_transformation_file(
        sample_output, write_strategy=write_strategy
    )
    write_strategy.assert_called_once()


def test_create_init_transformation_file_exists():
    sample_output = MagicMock(spec_set=pathlib.Path, exists=lambda *_: True)
    write_strategy = Mock()
    with pytest.raises(FileExistsError):
        resolve_authorized_terms.create_init_transformation_file(
            sample_output, write_strategy=write_strategy
        )
    write_strategy.assert_not_called()


def test_resolve_authorized_terms_calls_resolve_strategy():
    sample_input_tsv = MagicMock(spec_set=pathlib.Path, exists=lambda *_: True)
    sample_transformation_tsv = MagicMock(
        spec_set=pathlib.Path, exists=lambda *_: True
    )
    output_file = MagicMock(spec_set=pathlib.Path, exists=lambda *_: False)
    resolve_strategy = Mock(return_value=[
        (
            galatea.tsv.TableRow(line_number=1, entry={"element1": "value1"}),
            galatea.tsv.TableRow(line_number=1, entry={"element1": "value2"}),
         )
    ])

    resolve_authorized_terms.resolve_authorized_terms(
        sample_input_tsv,
        transformation_file=sample_transformation_tsv,
        output_file=output_file,
        resolve_strategy=resolve_strategy,
    )
    resolve_strategy.assert_called_once()
    output_file.open.assert_called_once_with("w")


@pytest.mark.parametrize(
    "input_data, expected_new_data",
    [
        (
            [
                TableRow(
                    line_number=1, entry={"260$a": "hello", "264$a": "eggs"}
                )
            ],
            [
                TableRow(
                    line_number=1, entry={"260$a": "hello", "264$a": "eggs"}
                )
            ],
        ),
        # Notice that spam. is changed to Spam
        (
            [
                TableRow(
                    line_number=1, entry={"260$a": "spam.", "264$a": "eggs"}
                )
            ],
            [
                TableRow(
                    line_number=1, entry={"260$a": "Spam", "264$a": "eggs"}
                )
            ],
        ),
        # Notice that spam. is not changed to Spam because it's not part of the
        # fields to resolve
        (
            [
                TableRow(
                    line_number=1,
                    entry={
                        "261$a": "spam.",
                        "260$a": "bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
            [
                TableRow(
                    line_number=1,
                    entry={
                        "261$a": "spam.",
                        "260$a": "bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
        ),
        (
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "bacon.||bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "bacon.||bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
        ),
        # Test that multiple values are handled correctly
        (
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "spam.||bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "Spam||bacon.",
                        "264$a": "eggs",
                    },
                )
            ],
        ),
        # Test that empty values are handled correctly
        (
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "bacon||",
                        "264$a": "eggs",
                    },
                )
            ],
            [
                TableRow(
                    line_number=1,
                    entry={
                        "260$a": "bacon||",
                        "264$a": "eggs",
                    },
                )
            ],
        ),
    ],
)
def test_iter_resolved_terms_new_data(input_data, expected_new_data):
    assert [
        entry[1]
        for entry in resolve_authorized_terms.iter_resolved_terms(
            input_data,
            transformer=resolve_authorized_terms.Transform(
                io.StringIO(
                    "unauthorized term\tresolving authorized term\n"
                    "spam.\tSpam\n"
                )
            ),
            fields_to_resolve={"260$a", "264$a"},
        )
    ] == expected_new_data


def test_diff_rows():
    row_a = {
        "260$a": "hello",
        "264$a": "eggs",
    }
    row_b = {
        "260$a": "hello",
        "264$a": "Spam",
    }
    assert resolve_authorized_terms.diff_rows(row_a, row_b) == {
        "264$a": ("eggs", "Spam")
    }


def test_create_row_diff_report():
    row_a = TableRow(
        line_number=1,
        entry={
            "260$a": "hello",
            "264$a": "eggs",
        },
    )
    row_b = TableRow(
        line_number=1,
        entry={
            "260$a": "hello",
            "264$a": "Spam",
        },
    )
    assert (
        resolve_authorized_terms.create_row_diff_report(row_a, row_b).strip()
        == """  Line: 1. Key: 264$a :
- eggs
+ Spam
________________________________________________________________________________
""".strip()
    )
