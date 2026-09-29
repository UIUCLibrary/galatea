import csv
import logging
import pathlib
from unittest.mock import Mock, create_autospec

import pytest

from galatea.utils import GalateaException
from galatea import tsv as galatea_tsv

galatea_qml = pytest.importorskip("galatea.gui.qml")
galatea_backend = pytest.importorskip("galatea.gui.qml.backend")
QtCore = pytest.importorskip("PySide6.QtCore")


class TestBackend:
    @pytest.mark.parametrize(
        "side_effect, expect_return",
        [(None, True), (GalateaException("something went wrong"), False)],
    )
    def test_load_model_from_file(
        self, side_effect, expect_return, monkeypatch
    ):
        backend = galatea_backend.Backend()
        mock_load_tsv_strategy = create_autospec(
            galatea_backend.Backend.LoadTsvProtocol, side_effect=side_effect
        )
        monkeypatch.setattr(
            galatea_backend.Backend,
            "load_tsv_strategy",
            mock_load_tsv_strategy,
        )

        assert (
            backend.load_model_from_file(
                file_path=Mock(
                    name="file_path",
                    spec_set=QtCore.QUrl,
                    path=Mock(return_value="/some/path"),
                ),
                dialect=csv.excel_tab,
                tsv_model=Mock(
                    name="tsv_model", spec_set=galatea_qml.models.TsvModel
                ),
            )
            is expect_return
        )

    def test_load_model_from_file_logs_exception(self, caplog, monkeypatch):
        backend = galatea_backend.Backend()
        mocked_load_tsv_strategy = create_autospec(
            galatea_backend.Backend.LoadTsvProtocol,
            side_effect=GalateaException("something went wrong"),
        )

        monkeypatch.setattr(
            galatea_backend.Backend,
            "load_tsv_strategy",
            mocked_load_tsv_strategy,
        )

        with caplog.at_level(logging.ERROR):
            assert (
                backend.load_model_from_file(
                    file_path=Mock(
                        name="file_path",
                        spec_set=QtCore.QUrl,
                        path=Mock(return_value="/some/path"),
                    ),
                    dialect=csv.excel_tab,
                    tsv_model=Mock(
                        name="tsv_model", spec_set=galatea_qml.models.TsvModel
                    ),
                )
                is False
            )
        assert "Unable to open file" in caplog.text

    def test_save_model_to_file(self, monkeypatch):
        backend = galatea_backend.Backend()
        mock_export_model_data_strategy = create_autospec(
            galatea_backend.Backend.ExportModelDataProtocol,
            return_value=(
                ["header1", "header2"],
                [{"header1": "value1", "header2": "value2"}],
            ),
        )
        monkeypatch.setattr(
            galatea_backend.Backend,
            "export_model_data_strategy",
            mock_export_model_data_strategy,
        )
        mocked_save_tsv_strategy = create_autospec(
            galatea_backend.Backend.WriteTsvProtocol
        )
        monkeypatch.setattr(
            galatea_backend.Backend,
            "save_tsv_strategy",
            mocked_save_tsv_strategy,
        )

        assert (
            backend.save_model_to_file(
                file_path=Mock(
                    name="file_path",
                    spec_set=QtCore.QUrl,
                    path=Mock(return_value="/some/path"),
                ),
                dialect=csv.excel_tab,
                tsv_model=Mock(
                    name="tsv_model",
                    spec_set=galatea_qml.models.TsvModel,
                ),
            )
            is True
        )

    def test_get_dialect(self, monkeypatch):
        backend = galatea_backend.Backend()
        mocked_get_dialect_strategy = create_autospec(
            galatea_backend.Backend.GetTSVDialectProtocol,
            return_value=csv.excel_tab,
        )
        monkeypatch.setattr(
            galatea_backend.Backend,
            "get_dialect_strategy",
            mocked_get_dialect_strategy,
        )
        assert (
            backend.get_dialect(
                file_path=Mock(
                    name="file_path",
                    spec_set=QtCore.QUrl,
                    path=Mock(return_value="/some/path"),
                )
            )
            is csv.excel_tab
        )


def test_get_tsv_dialect():
    path = create_autospec(pathlib.Path)
    assert (
        galatea_backend.get_tsv_dialect(
            path, detection_strategy=Mock(return_value=csv.excel_tab)
        )
        is csv.excel_tab
    )


@pytest.mark.parametrize(
    "data,file_string_data",
    [
        (
            [
                galatea_tsv.TableRow(
                    line_number=1, entry={"col1": "val1", "col2": "val2"}
                )
            ],
            "",
        ),
        (
            [],
            """col1\tcol2
""",
        ),
    ],
)
def test_load_tsv(data, file_string_data, monkeypatch):
    monkeypatch.setattr(
        galatea_backend,
        "get_first_row_of_tsv",
        Mock(return_value=["col1", "col2"]),
    )

    path = create_autospec(pathlib.Path)
    dialect = csv.excel_tab
    model = create_autospec(galatea_qml.models.TsvModel)
    read_tsv_strategy = create_autospec(
        galatea_tsv.IterTsvFileProtocol, return_value=data
    )

    galatea_backend.load_tsv(
        path, dialect, model, read_tsv_rows_strategy=read_tsv_strategy
    )
    model.load_data.assert_called_once()


def test_get_first_row_of_tsv():
    path = create_autospec(pathlib.Path)
    # simulate that the tsv has only a single row for the header
    reader_strategy = create_autospec(
        csv.reader, return_value=iter([["col1", "col2"]])
    )

    assert galatea_backend.get_first_row_of_tsv(
        path,
        csv.excel_tab,
        tsv_reader_strategy=reader_strategy,
    ) == ["col1", "col2"]
