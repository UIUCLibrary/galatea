"""This launches a speedwagon application configured to run galatea."""

import logging
import os
import sys

import argparse

import speedwagon.startup
import speedwagon.config.config
from galatea.utils import get_version

# =============================================================================
# ENVIRONMENT_VARIABLE_NAMES

ENVIRONMENT_VAR_NAME_CONFIG_DIRECTORY_NAME = "GALATEA_CONFIG_DIRECTORY_NAME"
# set this environment variable to change the prefix name of config file.
# Note: It will still in the home directory, just with a different name other
# than the default


# =============================================================================
#  Defaults

DEFAULT_CONFIG_DIRECTORY_NAME = "galatea-speedwagon"

# =============================================================================

# Constants
DEFAULT_CONFIG_DATA = """
[GLOBAL]
starting-tab = All
debug = False

[PLUGINS.galatea.gui.speedwagon_plugin]
galatea_workflows = True

""".strip()

DEFAULT_TABS_DATA = """
Authorized Terms:
- 'Authorized Terms: Check'
- 'Authorized Terms: New Transformation file'
- 'Authorized Terms: Resolve'
Clean TSV:
- Clean TSV
Merge Data:
- 'Merge Data: Initialize GetMarc Mapper File'
- 'Merge Data: Merge from GetMarc'
""".strip()

bootstrap_logger = logging.getLogger("bootstrap_speedwagon")


def verify_plugin_start(config_file_location) -> None:
    """Create boilerplate config file if not already present."""
    app_data_directory = config_file_location["app_data_directory"]

    if not os.path.exists(app_data_directory):
        os.makedirs(app_data_directory)

    config_ini = os.path.join(
        app_data_directory,
        speedwagon.config.config.CONFIG_INI_FILE_NAME,
    )
    if not os.path.exists(config_ini):
        with open(config_ini, "w", encoding="utf-8") as f:
            bootstrap_logger.info(f"Creating a new config file: {config_ini}")
            f.write(DEFAULT_CONFIG_DATA)
            f.write("\n")


def set_tabs(config_file_location) -> None:
    """Create customized tabs file if not already present."""
    tab_file = config_file_location["tab_config_file"]
    if not os.path.exists(tab_file):
        bootstrap_logger.info(f"Creating initial tabs file: {tab_file}")
        with open(
            config_file_location["tab_config_file"], "w", encoding="utf-8"
        ) as f:
            f.write(DEFAULT_TABS_DATA)
            f.write("\n")


DEFAULT_STARTUP_TASKS = [
    lambda _, config_file_location: verify_plugin_start(config_file_location),
    lambda _, config_file_location: set_tabs(config_file_location),
]


def run_speedwagon(
    argv=None,
    statup_tasks=None,
    app_launcher_klass=speedwagon.startup.ApplicationLauncher,
) -> int:
    """Launch a speedwagon application configured to run galatea commands."""
    speedwagon_parser = speedwagon.config.config.CliArgsSetter.get_arg_parser()

    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[speedwagon_parser],
        conflict_handler="resolve",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    argv = argv or sys.argv
    if "--verbose" in argv:
        logging_level = logging.DEBUG

        # IMPORTANT: The current line is there because without it, arg parse
        # will fail because "--verbose" is not a flag being used by
        # speedwagon. If we even support the "--verbose" flag in anything
        # else, please remove the following line.
        argv.remove("--verbose")
    else:
        logging_level = logging.INFO

    bootstrap_logger.setLevel(logging_level)
    bootstrap_log_handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    bootstrap_log_handler.setFormatter(formatter)

    bootstrap_logger.addHandler(bootstrap_log_handler)

    args = parser.parse_args(argv[1:])
    if args.command is not None:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.addFilter(lambda rec: rec.levelno < logging.WARNING)
        speedwagon.startup.logger.addHandler(stdout_handler)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        speedwagon.startup.logger.addHandler(stderr_handler)

        speedwagon.startup.logger.setLevel(logging.INFO)
        try:
            speedwagon.startup.run_command(
                command_name=args.command, args=args
            )
        except BrokenPipeError:
            bootstrap_logger.error("Broken pipe error here")
            raise
        return 0

    app_launcher = app_launcher_klass()
    app_launcher.application_name = "Galatea"

    app_launcher.application_config_directory_name = os.getenv(
        ENVIRONMENT_VAR_NAME_CONFIG_DIRECTORY_NAME,
        DEFAULT_CONFIG_DIRECTORY_NAME,
    )

    app_launcher.startup_tasks = (
        statup_tasks if statup_tasks is not None else DEFAULT_STARTUP_TASKS
    )

    bootstrap_logger.debug("Initializing Speedwagon")
    app_launcher.initialize()
    bootstrap_logger.debug("Initializing Speedwagon - Done")
    bootstrap_logger.debug("Running Speedwagon with galatea configured...")
    try:
        return app_launcher.run()
    finally:
        bootstrap_logger.debug("Speedwagon closed")
