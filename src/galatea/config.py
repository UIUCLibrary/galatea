"""galatea.config."""

import abc
import pathlib
from typing import Optional
import dataclasses
import platform
import json

__all__ = ["get_config", "set_config", "get_default_config_file_path"]


@dataclasses.dataclass
class Config:
    get_marc_server_url: Optional[str] = None


class ConfigFileFormatStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_file_name() -> str:
        """Return the name of the configuration file."""

    @abc.abstractmethod
    def serialize(self, config: Config) -> str:
        """Serialize the configuration to a string."""

    @abc.abstractmethod
    def deserialize(self, config_str: str) -> Config:
        """Deserialize the configuration from a string."""


class JSONConfigStrategy(ConfigFileFormatStrategy):
    @staticmethod
    def get_file_name() -> str:
        return "config.json"

    def serialize(self, config: Config) -> str:
        """Serialize the configuration to a TOML string."""
        return json.dumps(
            {"get_marc_server_url": config.get_marc_server_url or ""}, indent=4
        )

    def deserialize(self, config_str: str) -> Config:
        """Deserialize the configuration from a TOML string."""
        data = json.loads(config_str)
        return Config(get_marc_server_url=data.get("get_marc_server_url"))


def get_format_strategy() -> ConfigFileFormatStrategy:
    return JSONConfigStrategy()


class ConfigStrategy(abc.ABC):
    def read_raw_data(self) -> str:
        with self.get_config_file_path().open() as config_file:
            return config_file.read()

    def write_raw_data(self, raw_data: str) -> None:
        with self.get_config_file_path().open("w") as config_file:
            config_file.write(raw_data)

    @abc.abstractmethod
    def get_config_file_path(self) -> pathlib.Path:
        """Return the path to the configuration file."""

    @abc.abstractmethod
    def read(self) -> Config:
        """Load the configuration."""

    @abc.abstractmethod
    def write(self, data: Config) -> None:
        """Write the configuration."""


class HomeDirectoryConfigStrategy(ConfigStrategy):
    """Configuration strategy that stores config data on home directory."""

    def __init__(
        self, config_format_strategy: Optional[ConfigFileFormatStrategy] = None
    ):
        super().__init__()
        self.config_format_strategy: ConfigFileFormatStrategy = (
            config_format_strategy or get_format_strategy()
        )

    def get_config_file_path(self) -> pathlib.Path:
        return (
            pathlib.Path.home()
            / ".config"
            / "galatea"
            / self.config_format_strategy.get_file_name()
        )

    def read(self) -> Config:
        return self.config_format_strategy.deserialize(self.read_raw_data())

    def write(self, data: Config):
        self.write_raw_data(self.config_format_strategy.serialize(data))


config_strategies = {
    "Darwin": HomeDirectoryConfigStrategy(),
    "Linux": HomeDirectoryConfigStrategy(),
    "Windows": HomeDirectoryConfigStrategy(),
}


def _get_config_strategy(platform_name: str) -> ConfigStrategy:
    platform_name = platform_name or platform.system()
    locate_config_file_strategy = config_strategies.get(platform_name)
    if locate_config_file_strategy is None:
        raise ValueError(f"Unsupported platform: {platform_name}")
    return locate_config_file_strategy


def get_default_config_file_path() -> pathlib.Path:
    """Get the default path to the configuration file based on the platform."""
    return _get_config_strategy(platform.system()).get_config_file_path()


def get_config(
    locate_config_file_strategy: Optional[ConfigStrategy] = None,
    platform_name: Optional[str] = None,
):
    """Get the configuration data."""
    locate_config_file_strategy = (
        locate_config_file_strategy
        or _get_config_strategy(platform_name or platform.system())
    )
    return locate_config_file_strategy.read()


def set_config(
    data: Config,
    locate_config_file_strategy: Optional[ConfigStrategy] = None,
    platform_name: Optional[str] = None,
):
    """Set the configuration data."""
    locate_config_file_strategy = (
        locate_config_file_strategy
        or _get_config_strategy(platform_name or platform.system())
    )
    locate_config_file_strategy.write(data)
