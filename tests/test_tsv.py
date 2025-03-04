import io
import pathlib
from unittest.mock import create_autospec, Mock, patch, mock_open, ANY

import galatea.tsv
import csv

import pytest

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
        galatea.tsv.write_tsv_fp(
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
        galatea.tsv.write_tsv_fp(
            buffer, data=[], dialect=csv.get_dialect("excel-tab")
        )
        buffer.seek(0)
        result = buffer.read()
        assert result == ""


def test_write_tsv_file():
    writing_strategy = create_autospec(galatea.tsv.write_tsv_fp)
    data = Mock(name="data")
    dialect = csv.get_dialect("excel-tab")
    with patch("galatea.tsv.open", mock_open()):
        galatea.tsv.write_tsv_file(
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
                galatea.tsv.iter_tsv_fp(
                    sample_tsv_file_pointer, dialect=csv.get_dialect("excel-tab")
                )
            ).entry["1"]
            == "99160807512205899"
    )


def test_iter_tsv_file_calls_strategy():
    strategy = Mock(return_value=[])
    with patch("galatea.tsv.open", mock_open(read_data="")):
        list(
            galatea.tsv.iter_tsv_file(
                "spam.tsv",
                dialect=csv.get_dialect("excel-tab"),
                strategy=strategy,
            )
        )
    strategy.assert_called_once()

def test_get_tsv_dialect(sample_tsv_file_pointer):
    assert galatea.tsv.get_tsv_dialect(sample_tsv_file_pointer).delimiter == "\t"


def test_get_tsv_dialect_fallback_to_excel_tab():
    with io.StringIO() as buff:
        buff.write("""1	50	100	110	111	245	246	255	260$a	264$a	260$b	264$b	260$c	264$c	300$ab	300$c	500	650$a	650$x	651$a	650$z	650$v	651$v	650$y	655	600	610	611	700	710	711
99160807512205899	G4041.R2 1987.U55		United States.Army.Corps of Engineers.North Central Division.		Division and district boundaries /North Central Division, Corps of Engineers, U S Army.		Scale 1:5,000,000 ;polyconic projection(W 104°--W 70°/N 50°10ʹ--N 38°).	[Chicago, Ill.?] :		The Division,		[1987]		1 map : color ;	26 x 51 cm	Shipping list no.: 88-22-P.||"1 October 1987."||"U.S.G.P.O. : 1987-542-715."	Strategic aspects of individual places		Middle West||Middle West			Maps.		Maps--fast--(OCoLC)fst01423704||Maps.--lcgft||Cartes géographiques.--rvmgf--(CaQQLa)RVMGF-000000197		United States.--Army.--Corps of Engineers.--North Central Division.||United States.--Army.--Corps of Engineers.--North Central Division--fast--(OCoLC)fst00559145""")
        buff.seek(0)
        detections_strategy = Mock(side_effect=galatea.tsv.UnknownDialect())
        res = galatea.tsv.get_tsv_dialect(
            buff, detection_strategy=detections_strategy
        )
        assert res == csv.get_dialect("excel-tab")


def test_get_tsv_dialect_resets_fp(sample_tsv_file_pointer):
    sample_tsv_file_pointer.seek(10)
    galatea.tsv.get_tsv_dialect(sample_tsv_file_pointer)
    assert sample_tsv_file_pointer.tell() == 10


def test_remembered_file_pointer_head(sample_tsv_file_pointer):
    sample_tsv_file_pointer.seek(10)
    with galatea.tsv.remembered_file_pointer_head(sample_tsv_file_pointer) as fp:
        galatea.tsv.get_tsv_dialect(fp)
    assert sample_tsv_file_pointer.tell() == 10



def test_get_field_names_calls_fp_strategy():
    strategy = Mock()
    with patch("galatea.tsv.open", mock_open()):
        galatea.tsv.get_field_names("somepath", "excel-tab", strategy)
    strategy.assert_called_once()


def test_get_field_names_fp():
    with io.StringIO() as buff:
        buff.write(
            "1	50	100	110	111	245	246	255	260$a"
        )
        buff.seek(0)
        assert galatea.tsv.get_field_names_fp(buff, dialect="excel-tab") == [
            "1",
            "50",
            "100",
            "110",
            "111",
            "245",
            "246",
            "255",
            "260$a",
        ]


def test_get_field_names_fp_raise_if_no_field_names_found():
    with pytest.raises(ValueError):
        with io.StringIO() as buff:
            galatea.tsv.get_field_names_fp(buff, dialect="excel-tab")
