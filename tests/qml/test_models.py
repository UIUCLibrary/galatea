import pathlib
import warnings
from unittest.mock import Mock
import csv
import pytest
from galatea import tsv

models = pytest.importorskip("galatea.gui.qml.models")
QtCore = pytest.importorskip("PySide6.QtCore")


@pytest.mark.parametrize(
    "column_order, data, expected_size",
    [
        (["Column1"], [{"Column1": "Value1"}], 1),
        (["Column1"], [{"Column1": "Value1"}, {"Column1": "Value2"}], 2),
        (
            ["Column1", "Column2"],
            [{"Column1": "Value1", "Column2": "Value2"}],
            1,
        ),
    ],
)
def test_load_model(column_order, data, expected_size):
    model = models.TsvModel()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        model.load_data(column_order, data)
    assert model.rowCount() == expected_size


@pytest.mark.parametrize(
    "input_data",
    [
        (
            ["Column1"],
            [tsv.TableRow(line_number=1, entry={"Column1": "Value1"})],
        ),
        (["Column1"], []),
        (
            ["Column1", "Column2"],
            [
                tsv.TableRow(
                    line_number=1,
                    entry={"Column1": "Value1", "Column2": "Value2"},
                )
            ],
        ),
    ],
)
def test_export_data(input_data: tuple[list[str], list[tsv.TableRow]]):
    model = models.TsvModel()
    columns, data = input_data
    models.load_tsv_model(model, columns, data)
    assert models.export_data(model) == (columns, [row.entry for row in data])


class TestTsvModel:
    def test_set_data_with_unsupported_role_does_not_crash(self):
        model = models.TsvModel()
        index = model.index(0, 0)
        model.setData(index, "", -1)

    def test_insert_columns(self):
        model = models.TsvModel()
        assert model.insertColumns(0, 1) is True
        assert model.columnCount() == 1

    def test_set_column_name_for_invalid_column_is_false(self):
        model = models.TsvModel()
        assert model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1") is False

    def test_set_row_header_returns_false(self):
        model = models.TsvModel()
        # reserving row header for line number, don't let user update it
        assert model.setHeaderData(0, QtCore.Qt.Vertical, "Row1") is False

    def test_set_column_name(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        assert model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1") is True
        assert model.columns_order[0] == "Column1"

    def test_unset_header_is_column_index_plus_one(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        assert model.headerData(0, QtCore.Qt.Horizontal) == 1

    def test_header_data_for_unsupported_role_is_none(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        assert model.headerData(0, QtCore.Qt.Horizontal, -1) is None

    def test_flags(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        index = model.index(0, 0)
        assert QtCore.Qt.ItemIsEnabled in model.flags(index)

    def test_insert_rows(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        assert model.rowCount() == 0
        model.insertRows(0, 1)
        assert model.rowCount() == 1

    def test_insert_rows_with_existing_data(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        assert model.rowCount() == 0
        model.insertRows(0, 1)
        model.setData(model.index(0, 0), "test", QtCore.Qt.EditRole)
        assert model.rowCount() == 1
        model.insertRows(0, 5)
        assert model.rowCount() == 6
        assert model.data(model.index(5, 0)) == "test"

    def test_insert_multiple_rows(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        assert model.rowCount() == 0
        model.insertRows(0, 10)
        assert model.rowCount() == 10

    def test_set_data(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        model.insertRows(0, 1)
        index = model.index(0, 0)
        assert model.setData(index, "test", QtCore.Qt.EditRole) is True

    def test_data_with_invalid_index(self):
        model = models.TsvModel()
        index = model.index(0, 0)

        # this is an empty table and there is no first row
        assert model.data(index) is None

    def test_data_with_unimplemented_role(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        model.insertRows(0, 1)

        index = model.index(0, 0)
        assert model.data(index, -1) is None

    def test_data(self):
        model = models.TsvModel()
        model.insertColumns(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Column1")
        model.insertRows(0, 1)
        model.setData(model.index(0, 0), "test", QtCore.Qt.EditRole)
        assert model.data(model.index(0, 0)) == "test"

    def test_removeRow(self):
        model = models.TsvModel()
        models.load_tsv_model(
            model,
            column_order=["name", "value"],
            data=[
                tsv.TableRow(
                    line_number=1, entry={"name": "Test", "value": "test"}
                )
            ],
        )
        assert model.rowCount() == 1
        assert model.removeRow(0) is True
        assert model.rowCount() == 0

    def test_removeColumns(self):
        model = models.TsvModel()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            model.load_data(
                column_order=["name", "value"],
                data=[{"name": "Test", "value": "test"}],
            )
        assert model.columnCount() == 2
        assert model.removeColumn(0) is True
        assert model.columnCount() == 1
        assert model.headerData(0, QtCore.Qt.Horizontal) == "value"


def test_load_tsv_model():
    model = models.TsvModel()
    models.load_tsv_model(
        model,
        column_order=["name", "value"],
        data=[
            tsv.TableRow(
                line_number=1, entry={"name": "spam", "value": "bacon"}
            )
        ],
    )
    assert model.columnCount() == 2
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0)) == "spam"


def test_loaded_tsv_model_has_source():
    model = models.TsvModel()
    models.load_tsv_model(
        model,
        column_order=["name", "value"],
        data=[
            tsv.TableRow(
                line_number=1, entry={"name": "spam", "value": "bacon"}
            )
        ],
    )
    assert model.data(model.index(0, 0), model.SourceRole) is not None


def test_load_tsv_file_to_inspector(qtbot):
    iter_tsv_data_strategy = Mock(
        return_value=[(1, ["spam", "bacon"]), (2, ["eggs", "eggs and bacon"])]
    )
    file = QtCore.QUrl("path/to/test.tsv")
    inspector = models.TsvInspector()
    private_data = models.PrivateTsvInspectorData()
    with qtbot.waitSignal(inspector.dataChanged):
        models.load_tsv_file_to_inspector(
            file, private_data, inspector, iter_tsv_data_strategy
        )


def test_load_tsv_file_to_inspector_error_clears_rows(qtbot):
    iter_tsv_data_strategy = Mock(
        side_effect=RuntimeError("Error reading file")
    )
    file = QtCore.QUrl("path/to/test.tsv")
    private_data = models.PrivateTsvInspectorData(
        tsv_rows={1: ["spam", "bacon"], 2: ["eggs", "eggs and bacon"]}
    )
    inspector = models.TsvInspector()
    with pytest.raises(RuntimeError):
        models.load_tsv_file_to_inspector(
            file, private_data, inspector, iter_tsv_data_strategy
        )
    assert len(private_data.tsv_rows) == 0


class TestTsvInspector:
    @pytest.mark.parametrize(
        "element,expected",
        [
            (models.TsvElementData("something"), True),
            (
                models.TsvElementData(
                    "something", source=models.TSVReference(1, 2)
                ),
                True,
            ),
            (
                models.TsvElementData(
                    "something", source=models.TSVReference(1, 2)
                ),
                False,
            ),
            (None, True),
        ],
    )
    def test_entryHasChanged(self, element, expected):
        inspector = models.TsvInspector()
        compare_strategy = Mock(return_value=expected)
        assert (
            inspector.entryHasChanged(
                element, compare_strategy=compare_strategy
            )
            is expected
        )

    def test_state_object_starts_with_empty_state(self):
        inspector = models.TsvInspector()
        assert isinstance(
            inspector.state_object, models.TsvInspectorEmptyState
        )
        assert inspector.get_current_state_name() == "Empty"

    def test_setting_dialect(self):
        inspector = models.TsvInspector()
        inspector.set_dialect(csv.excel_tab)
        assert inspector.get_dialect() == csv.excel_tab

    def test_setting_file(self):
        inspector = models.TsvInspector()
        tsv_file = QtCore.QUrl("somefile.tsv")
        strategy = Mock()
        inspector.set_file(tsv_file, strategy)
        strategy.assert_called_once_with(tsv_file)

    def test_get_file(self):
        inspector = models.TsvInspector()
        strategy = Mock()
        inspector.get_file(strategy)
        strategy.assert_called_once()

    @pytest.mark.parametrize("is_file", [True, False])
    def test_dataIsDifferent(self, monkeypatch, is_file):
        inspector = models.TsvInspector(file=QtCore.QUrl("somefile.tsv"))
        model = Mock()
        compare_strategy = Mock(return_value=False)
        monkeypatch.setattr(
            pathlib.Path, "is_file", Mock(return_value=is_file)
        )
        assert inspector.dataIsDifferent(model, compare_strategy) is False

    def test_reloadFile(self):
        inspector = models.TsvInspector()
        strategy = Mock()
        inspector.reloadFile(strategy)
        strategy.assert_called_once()

    def test_value_is_different(self):
        inspector = models.TsvInspector()
        compare_strategy = Mock(return_value=True)
        result = inspector.value_is_different("value", 1, 2, compare_strategy)
        compare_strategy.assert_called_once()
        assert result is True


@pytest.mark.parametrize(
    "state_klass, expect_name",
    [
        (models.TsvInspectorLoadingState, "Loading"),
        (models.TsvInspectorLoadedState, "Loaded"),
        (models.TsvInspectorEmptyState, "Empty"),
    ],
)
def test_state_names(state_klass, expect_name):
    inspector = models.TsvInspector()
    state = state_klass(inspector)
    assert state.get_state_name() == expect_name


class TestTsvInspectorLoadingState:
    @pytest.fixture
    def state(self):
        inspector = models.TsvInspector()
        return models.TsvInspectorLoadingState(inspector)

    def test_set_file_is_noop(self, state, caplog):
        state.set_file("some file")
        assert len(caplog.records) == 1
        assert caplog.records[0].message == "Unable to set file while loading"

    def test_value_is_different_is_noop(self, state):
        assert state.value_is_different("something", 1, 2) is None

    def test_set_dialect_is_noop(self, state, caplog):
        state.set_dialect(csv.excel_tab)
        assert len(caplog.records) == 1
        assert caplog.records[0].message == "Unable to set file while loading"


class TestTsvInspectorEmptyState:
    @pytest.fixture
    def inspector(self):
        return models.TsvInspector()

    @pytest.fixture
    def state(self, inspector):
        return models.TsvInspectorEmptyState(inspector)

    def test_set_dialect(self, state, inspector):
        state.set_dialect(csv.excel)
        assert state.get_dialect() == csv.excel

    def test_set_file(self, state, monkeypatch):
        load_tsv_file_strategy = Mock()
        monkeypatch.setattr(
            models.TsvInspectorEmptyState,
            "load_tsv_file_strategy",
            load_tsv_file_strategy,
        )
        state.set_file(QtCore.QUrl("some file"))
        load_tsv_file_strategy.assert_called_once()

    #
    def test_value_is_true(self, state):
        assert state.value_is_different("something", 1, 2) is True


class TestTsvInspectorLoadedState:
    @pytest.fixture
    def inspector(self):
        return models.TsvInspector()

    @pytest.fixture
    def state(self, inspector):
        return models.TsvInspectorLoadedState(inspector)

    def test_set_file(self, state, monkeypatch):
        strategy = Mock()
        monkeypatch.setattr(
            models.TsvInspectorLoadedState,
            "load_tsv_file_to_inspector_strategy",
            strategy,
        )
        state.set_file("some file")
        strategy.assert_called_once()

    def test_reload_file(self, state, monkeypatch):
        strategy = Mock()
        monkeypatch.setattr(
            models.TsvInspectorLoadedState,
            "load_tsv_file_to_inspector_strategy",
            strategy,
        )
        state.reload_file()
        strategy.assert_called_once()

    def test_value_is_different(self, state, monkeypatch):
        strategy = Mock()
        monkeypatch.setattr(
            models.TsvInspectorLoadedState,
            "compare_value_strategy",
            strategy,
        )
        state.value_is_different("something", 1, 2)
        strategy.assert_called_once()

    def test_set_dialect(self, state, inspector):
        state.set_dialect(csv.excel)
        assert state.get_dialect() == csv.excel


def test_compare_value():
    assert models.compare_value("my_value", 1, 2, ["some", "my_value"])


@pytest.fixture
def sample_model_factory():
    def make_model(column_names=None, rows=None):
        if column_names is None:
            column_names = []
        if rows is None:
            rows = []
        test_model = models.TsvModel()
        test_model.insertColumns(0, len(column_names))
        for i, column_name in enumerate(column_names):
            test_model.setHeaderData(i, QtCore.Qt.Horizontal, column_name)

        test_model.insertRows(0, len(rows))
        for row_index, row in enumerate(rows):
            for column_index, data in enumerate(row):
                index = test_model.index(row_index, column_index)
                test_model.setData(index, data)

        return test_model

    return make_model


def test_compare_tsv_model_to_data_rows(sample_model_factory):
    model = sample_model_factory(
        column_names=["my_header"], rows=[("my_data",)]
    )
    assert (
        models.compare_tsv_model_to_data_rows(model, {1: "my_header"}) is True
    )


def test_is_model_modified_with_no_inspector_is_true(sample_model_factory):
    model = sample_model_factory(
        column_names=["my_header"], rows=[("my_data",)]
    )
    index = model.index(0, 0)
    assert models.is_model_modified(model, index) is True


def test_is_model_modified_with_inspector(sample_model_factory):
    model = sample_model_factory(
        column_names=["my_header"], rows=[("my_data",)]
    )
    index = model.index(0, 0)
    inspector = Mock(
        spec_set=models.TsvInspector, entryHasChanged=Mock(return_value=False)
    )
    assert models.is_model_modified(model, index, inspector) is False
