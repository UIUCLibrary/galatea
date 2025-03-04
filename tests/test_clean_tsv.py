import pathlib
from unittest.mock import Mock, mock_open, patch, ANY, create_autospec

import pytest
import galatea.tsv
import galatea.clean_tsv
from galatea import clean_tsv, modifiers
import io

def test_make_empty_strings_none_removes_empty_strings():
    record = {"1": "somedata", "50": ""}
    assert clean_tsv.make_empty_strings_none(record)["50"] is None


def test_make_empty_strings_none_leaves_nonempty_strings():
    record = {"1": "somedata", "50": ""}
    assert clean_tsv.make_empty_strings_none(record)["1"] == "somedata"


def test_clean_tsv(monkeypatch):
    write_tsv_file = Mock(name="write_tsv_file")
    monkeypatch.setattr(clean_tsv, "write_tsv_file", write_tsv_file)
    monkeypatch.setattr(galatea.tsv, "get_field_names", Mock(return_value=[]))
    with patch("galatea.clean_tsv.open", mock_open(read_data="")):
        clean_tsv.clean_tsv(
            pathlib.Path("source.tsv"), pathlib.Path("output.tsv")
        )
    write_tsv_file.assert_called_once()


@pytest.fixture
def marc_entry():
    return {
        "1": "99160807512205899",
        "50": "G4041.R2 1987.U55",
        "100": None,
        "110": "United States.Army.Corps of Engineers.North Central Division.",
        "111": None,
        "245": "Division and district boundaries /North Central Division, Corps of Engineers, U S Army.",
        "246": None,
        "255": "Scale 1:5,000,000 ;polyconic projection(W 104°--W 70°/N 50°10ʹ--N 38°).",
        "260$a": "[Chicago, Ill.?] :",
        "264$a": None,
        "260$b": "The Division,",
        "264$b": None,
        "260$c": "[1987]",
        "264$c": None,
        "300$ab": "1 map : color ;",
        "300$c": "26 x 51 cm",
        "500": 'Shipping list no.: 88-22-P.||"1 October 1987."||"U.S.G.P.O. : 1987-542-715."',
        "650$a": "Strategic aspects of individual places",
        "650$x": None,
        "651$a": "Middle West||Middle West",
        "650$z": None,
        "650$v": None,
        "651$v": "Maps.",
        "650$y": None,
        "655": "Maps--fast--(OCoLC)fst01423704||Maps.--lcgft||Cartes géographiques.--rvmgf--(CaQQLa)RVMGF-000000197",
        "600": None,
        "610": "United States.--Army.--Corps of Engineers.--North Central Division.||United States.--Army.--Corps of Engineers.--North Central Division--fast--(OCoLC)fst00559145",
        "611": None,
        "700": None,
        "710": None,
        "711": None,
    }


def test_row_modifier(marc_entry):
    assert marc_entry != clean_tsv.row_modifier(marc_entry)


def test_row_modifier_removes_dups(marc_entry):
    assert clean_tsv.row_modifier(marc_entry)["651$a"] == "Middle West"


def test_row_modifier_removes_double_dashes(marc_entry):
    assert "--lcgft" not in clean_tsv.row_modifier(marc_entry)["655"]


def test_transform_row_and_merge(marc_entry):
    merged_row = clean_tsv.transform_row_and_merge(
        marc_entry,
        row_transformation_strategy=lambda *args, **kwargs: {"246": "dummy"},
    )
    assert (
        merged_row["246"] == "dummy" and merged_row["1"] == "99160807512205899"
    )


class TestRowTransformer:
    def test_no_transform(self, marc_entry):
        transformer = clean_tsv.RowTransformer()
        assert transformer.transform(marc_entry) == marc_entry

    def test_add_transformation_to_all_field(self, marc_entry):
        transformer = clean_tsv.RowTransformer()

        transformer.add_transformation(modifiers.remove_trailing_periods)
        transformed = transformer.transform(marc_entry)
        assert all(
            [
                # the original value ends with a period
                marc_entry["245"][-1] == ".",
                marc_entry["110"][-1] == ".",
                # the transformed value does not end with a period
                transformed["245"][-1] != ".",
                transformed["110"][-1] != ".",
            ]
        ), f"""original["245"] = {marc_entry["245"]}
                transformed['245'] = {transformed["245"]}"""

    def test_add_transformation_to_specific_field(self, marc_entry):
        transformer = clean_tsv.RowTransformer()
        transformer.add_transformation(
            modifiers.remove_trailing_periods,
            condition=lambda key, _: key == "245",
        )
        assert all(
            [
                # the original value ends with a period
                marc_entry["245"][-1] == ".",
                marc_entry["110"][-1] == ".",
                # only the entry with 245 key transformed value to remove a period
                transformer.transform(marc_entry)["245"][-1] != ".",
                transformer.transform(marc_entry)["110"][-1] == ".",
            ]
        )


def test_create_diff_report(marc_entry):
    row_a = clean_tsv.TableRow(line_number=1, entry=marc_entry)
    modified_data = marc_entry.copy()
    modified_data["260$b"] = "The Division"
    row_b = clean_tsv.TableRow(line_number=1, entry=modified_data)

    assert "260$b" in clean_tsv.create_diff_report(
        row_a, row_b, marc_entry.keys()
    )


def test_create_diff_report_no_changes(marc_entry):
    row_a = clean_tsv.TableRow(line_number=1, entry=marc_entry)
    row_b = clean_tsv.TableRow(line_number=1, entry=marc_entry)

    assert (
        clean_tsv.create_diff_report(row_a, row_b, marc_entry.keys()) is None
    )


def test_clean_tsv_row_diff_report_generator_called(monkeypatch, marc_entry):
    write_tsv_file = Mock(name="write_tsv_file")
    monkeypatch.setattr(galatea.tsv, "write_tsv_file", write_tsv_file)
    monkeypatch.setattr(
        galatea.tsv, "get_field_names", Mock(return_value=marc_entry.keys())
    )
    row_one = galatea.tsv.TableRow(1, marc_entry)
    monkeypatch.setattr(clean_tsv, "iter_tsv_fp", Mock(return_value=[row_one]))
    row_diff_report_generator = Mock()
    with patch("galatea.clean_tsv.open", mock_open(read_data="")):
        clean_tsv.clean_tsv(
            pathlib.Path("source.tsv"),
            pathlib.Path("output.tsv"),
            row_diff_report_generator=row_diff_report_generator,
        )
    row_diff_report_generator.assert_called_once_with(
        row_one, ANY, marc_entry.keys()
    )
