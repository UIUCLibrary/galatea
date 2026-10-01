import pytest

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
    model.load_data(column_order, data)
    assert model.rowCount() == expected_size


@pytest.mark.parametrize(
    "input_data",
    [
        (["Column1"], [{"Column1": "Value1"}]),
        (["Column1"], []),
        (["Column1", "Column2"], [{"Column1": "Value1", "Column2": "Value2"}]),
    ],
)
def test_export_data(input_data):
    model = models.TsvModel()
    model.load_data(*input_data)
    assert models.export_data(model) == input_data


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

    def test_modified(self):
        model = models.TsvModel()
        model.load_data(
            column_order=["name", "value"],
            data=[{"name": "Test", "value": "test"}],
        )
        assert model.isModified is False
        model.setData(model.index(0, 0), "new_value")
        assert (
            model.isModified is True
        ), "Model should be modified after setting data"
