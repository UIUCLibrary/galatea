import csv
import pathlib
from unittest.mock import Mock, mock_open, patch, ANY, create_autospec

import pytest

from galatea import clean_tsv
import io


def test_write_tsv_fp():
    with io.StringIO() as buff:
        data = [
            {
                "1": None,
                "50": None,
                "100": None,
                "110": None,
                "111": None,
                "245": None,
                "246": None,
                "255": None,
                "260$a": None,
                "264$a": None,
                "260$b": None,
                "264$b": None,
                "260$c": None,
                "264$c": None,
                "300$ab": None,
                "300$c": None,
                "500": None,
                "650$a": None,
                "650$x": None,
                "651$a": None,
                "650$z": None,
                "650$v": None,
                "651$v": None,
                "650$y": None,
                "655": None,
                "600": None,
                "610": None,
                "611": None,
                "700": None,
                "710": None,
                "711": None,
            }
        ]
        clean_tsv.write_tsv_fp(
            buff, data, dialect=csv.get_dialect("excel-tab")
        )
        buff.seek(0)
        result = buff.read()

    assert (
        result.strip()
        == "1	50	100	110	111	245	246	255	260$a	264$a	260$b	264$b	260$c	264$c	300$ab	300$c	500	650$a	650$x	651$a	650$z	650$v	651$v	650$y	655	600	610	611	700	710	711"
    )  # noqa: E501


def test_write_tsv_fp_empty_data():
    with io.StringIO() as buffer:
        clean_tsv.write_tsv_fp(
            buffer, data=[], dialect=csv.get_dialect("excel-tab")
        )
        buffer.seek(0)
        result = buffer.read()
        assert result == ""


def test_write_tsv_file():
    writing_strategy = create_autospec(clean_tsv.write_tsv_fp)
    data = Mock(name="data")
    dialect = csv.get_dialect("excel-tab")
    with patch("galatea.clean_tsv.open", mock_open()):
        clean_tsv.write_tsv_file(
            pathlib.Path("dummy.tsv"),
            data=data,
            dialect=dialect,
            writing_strategy=writing_strategy,
        )
        writing_strategy.assert_called_once_with(
            fp=ANY, data=data, dialect=dialect
        )


@pytest.fixture
def sample_tsv_file_pointer():
    sample_data = """1	50	100	110	111	245	246	255	260$a	264$a	260$b	264$b	260$c	264$c	300$ab	300$c	500	650$a	650$x	651$a	650$z	650$v	651$v	650$y	655	600	610	611	700	710	711
99160807512205899	G4041.R2 1987.U55		United States.Army.Corps of Engineers.North Central Division.		Division and district boundaries /North Central Division, Corps of Engineers, U S Army.		Scale 1:5,000,000 ;polyconic projection(W 104°--W 70°/N 50°10ʹ--N 38°).	[Chicago, Ill.?] :		The Division,		[1987]		1 map : color ;	26 x 51 cm	Shipping list no.: 88-22-P.||"1 October 1987."||"U.S.G.P.O. : 1987-542-715."	Strategic aspects of individual places		Middle West||Middle West			Maps.		Maps--fast--(OCoLC)fst01423704||Maps.--lcgft||Cartes géographiques.--rvmgf--(CaQQLa)RVMGF-000000197		United States.--Army.--Corps of Engineers.--North Central Division.||United States.--Army.--Corps of Engineers.--North Central Division--fast--(OCoLC)fst00559145				
"""  # noqa: E501
    with io.StringIO() as buff:
        buff.write(sample_data)
        buff.seek(0)
        yield buff


def test_iter_tsv_fp(sample_tsv_file_pointer):
    assert (
        next(
            clean_tsv.iter_tsv_fp(
                sample_tsv_file_pointer, dialect=csv.get_dialect("excel-tab")
            )
        )["1"]
        == "99160807512205899"
    )


def test_iter_tsv_file_calls_strategy():
    strategy = Mock(return_value=[])
    with patch("galatea.clean_tsv.open", mock_open(read_data="")):
        list(
            clean_tsv.iter_tsv_file(
                "spam.tsv",
                dialect=csv.get_dialect("excel-tab"),
                strategy=strategy,
            )
        )
    strategy.assert_called_once()


def test_apply_filters_calls_filter_function():
    filter_function = Mock()
    clean_tsv.apply_filters([filter_function], entry="dummy")
    filter_function.assert_called_once_with("dummy")


def test_make_empty_strings_none_removes_empty_strings():
    record = {"1": "somedata", "50": ""}
    assert clean_tsv.make_empty_strings_none(record)["50"] is None


def test_make_empty_strings_none_leaves_nonempty_strings():
    record = {"1": "somedata", "50": ""}
    assert clean_tsv.make_empty_strings_none(record)["1"] == "somedata"


def test_get_tsv_dialect(sample_tsv_file_pointer):
    assert clean_tsv.get_tsv_dialect(sample_tsv_file_pointer).delimiter == "\t"


def test_get_tsv_dialect_fallback_to_excel_tab():
    with io.StringIO() as buff:
        buff.write("""1	50	100	110	111	245	246	255	260$a	264$a	260$b	264$b	260$c	264$c	300$ab	300$c	500	650$a	650$x	651$a	650$z	650$v	651$v	650$y	655	600	610	611	700	710	711
99160807512205899	G4041.R2 1987.U55		United States.Army.Corps of Engineers.North Central Division.		Division and district boundaries /North Central Division, Corps of Engineers, U S Army.		Scale 1:5,000,000 ;polyconic projection(W 104°--W 70°/N 50°10ʹ--N 38°).	[Chicago, Ill.?] :		The Division,		[1987]		1 map : color ;	26 x 51 cm	Shipping list no.: 88-22-P.||"1 October 1987."||"U.S.G.P.O. : 1987-542-715."	Strategic aspects of individual places		Middle West||Middle West			Maps.		Maps--fast--(OCoLC)fst01423704||Maps.--lcgft||Cartes géographiques.--rvmgf--(CaQQLa)RVMGF-000000197		United States.--Army.--Corps of Engineers.--North Central Division.||United States.--Army.--Corps of Engineers.--North Central Division--fast--(OCoLC)fst00559145""")
        buff.seek(0)
        detections_strategy = Mock(side_effect=clean_tsv.UnknownDialect())
        res = clean_tsv.get_tsv_dialect(
            buff, detection_strategy=detections_strategy
        )
        assert res == csv.get_dialect("excel-tab")


def test_get_tsv_dialect_resets_fp(sample_tsv_file_pointer):
    sample_tsv_file_pointer.seek(10)
    clean_tsv.get_tsv_dialect(sample_tsv_file_pointer)
    assert sample_tsv_file_pointer.tell() == 10


def test_remembered_file_pointer_head(sample_tsv_file_pointer):
    sample_tsv_file_pointer.seek(10)
    with clean_tsv.remembered_file_pointer_head(sample_tsv_file_pointer) as fp:
        clean_tsv.get_tsv_dialect(fp)
    assert sample_tsv_file_pointer.tell() == 10


def test_clean_tsv(monkeypatch):
    write_tsv_file = Mock(name="write_tsv_file")
    monkeypatch.setattr(clean_tsv, "write_tsv_file", write_tsv_file)

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
