from unittest.mock import Mock

import pytest

from galatea.gui import main
import galatea.gui.bootstrap_speedwagon

editor = pytest.importorskip("galatea.gui.editor")


def test_run_table_frontend_main(monkeypatch):
    args = []
    main_func = Mock()
    monkeypatch.setattr(editor, "main", main_func)
    main.run_table_frontend(argv=args)
    main_func.assert_called_once_with(args)


def test_run_table_frontend_main_func():
    args = []
    main_func = Mock()
    main.run_table_frontend(argv=args, main_func=main_func)
    main_func.assert_called_once_with(args)


def test_run_speedwagon_frontend_main_func():
    main_func = Mock()
    args = []
    main.run_speedwagon_frontend(args, main_func=main_func)
    main_func.assert_called_once_with(args)


def test_test_run_speedwagon_frontend(monkeypatch):
    args = []
    run_speedwagon = Mock()
    monkeypatch.setattr(
        galatea.gui.bootstrap_speedwagon, "run_speedwagon", run_speedwagon
    )
    main.run_speedwagon_frontend(args)
    run_speedwagon.assert_called_once_with(args)


def test_main_uses_frontend_selector_strategy():
    frontend_selector_strategy = Mock()
    main.main(
        frontend_selector_strategy=Mock(
            return_value=frontend_selector_strategy
        )
    )
    frontend_selector_strategy.assert_called_once()


def test_main_returns_nonzero_on_import_error():
    frontend_selector_strategy = Mock(side_effect=ImportError)
    assert main.main(frontend_selector_strategy) != 0


@pytest.mark.parametrize("frontend", main.GUI_FRONTENDS)
def test_get_frontend(frontend):
    assert callable(main.get_frontend(frontend))


def test_get_frontend_with_invalid():
    with pytest.raises(ValueError):
        main.get_frontend("invalid_frontend")
