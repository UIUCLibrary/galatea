import pytest
from unittest.mock import Mock, ANY

bootstrap_speedwagon = pytest.importorskip("galatea.gui.bootstrap_speedwagon")


def test_verify_plugin_start_creates_new(tmp_path):
    galatea_config = tmp_path.joinpath("galatea_config")
    galatea_config.mkdir()
    bootstrap_speedwagon.verify_plugin_start({
        "app_data_directory": str(galatea_config)
    })
    assert (galatea_config / "config.ini").exists()


def test_verify_plugin_start_creates_new_with_directory(tmp_path):
    galatea_config_context = tmp_path.joinpath("galatea_config")
    galatea_config_context.mkdir()

    # Note: It isn't created yet, only mentioned
    galatea_config = galatea_config_context / "config_dir"

    bootstrap_speedwagon.verify_plugin_start({
        "app_data_directory": str(galatea_config)
    })
    assert (galatea_config / "config.ini").exists()


def test_set_tabs(tmp_path):
    galatea_config = tmp_path.joinpath("galatea_config")
    galatea_config.mkdir()

    bootstrap_speedwagon.set_tabs({
        "tab_config_file": str(galatea_config / "tabs.yml")
    })


@pytest.mark.parametrize("subcommand", ["info", "run"])
def test_run_speedwagon_subcommand(monkeypatch, subcommand):
    app_launcher = Mock()
    app_launcher_klass = Mock(return_value=app_launcher)
    mocked_run_command = Mock()
    monkeypatch.setattr(
        bootstrap_speedwagon.speedwagon.startup,
        "run_command",
        mocked_run_command,
    )
    bootstrap_speedwagon.run_speedwagon(
        argv=["galatea", subcommand],
        statup_tasks=[],
        app_launcher_klass=app_launcher_klass,
    )
    mocked_run_command.assert_called_once_with(
        command_name=subcommand, args=ANY
    )


def test_run_speedwagon(monkeypatch):
    app_launcher = Mock()
    app_launcher_klass = Mock(return_value=app_launcher)
    mocked_run_command = Mock()
    monkeypatch.setattr(
        bootstrap_speedwagon.speedwagon.startup,
        "run_command",
        mocked_run_command,
    )
    bootstrap_speedwagon.run_speedwagon(
        argv=["galatea"],
        statup_tasks=[],
        app_launcher_klass=app_launcher_klass,
    )
    app_launcher.run.assert_called_once()
