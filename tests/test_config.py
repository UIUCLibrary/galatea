import pathlib
from unittest.mock import Mock, MagicMock

import pytest

from galatea import config

def test_get_config():
    config_strategy = Mock(spec=config.ConfigStrategy)
    config.get_config(config_strategy)
    config_strategy.read.assert_called_once()

def test_set_config():
    config_strategy = Mock(spec=config.ConfigStrategy)
    some_data = {"spam": "eggs"}
    config.set_config(some_data, locate_config_file_strategy=config_strategy)
    config_strategy.write.assert_called_once_with(some_data)

def test_get_unsupported_platform():
    with pytest.raises(ValueError):
        config.get_config(platform_name="UnsupportedPlatform")

def test_set_unsupported_platform():
    with pytest.raises(ValueError):
        config.set_config(data={}, platform_name="UnsupportedPlatform")

class TestHomeDirectoryConfigStrategy:
    def test_get_config_file_path(self):
        strategy = config.HomeDirectoryConfigStrategy()
        assert "galatea" in str(strategy.get_config_file_path())

    def test_read(self):
        config_format_strategy = Mock(spec=config.ConfigFileFormatStrategy, get_file_name=Mock(return_value="test_config.toml"))

        strategy = config.HomeDirectoryConfigStrategy(config_format_strategy=config_format_strategy)
        strategy.read_raw_data = Mock(return_value="somedata")
        strategy.read()

        config_format_strategy.deserialize.assert_called_once_with("somedata")

    def test_write_calls_serialized(self):
        config_format_strategy = Mock(spec=config.ConfigFileFormatStrategy)
        strategy = config.HomeDirectoryConfigStrategy(config_format_strategy=config_format_strategy)
        strategy.write_raw_data = Mock(name='write_raw_data')
        strategy.write({"spam": "eggs"})
        config_format_strategy.serialize.assert_called_once_with({"spam": "eggs"})

class TestJSONConfigStrategy:
    def test_serialize(self):
        config_format = config.JSONConfigStrategy()
        current_config = config.Config(
            get_marc_server_url="some_url",
        )
        assert config_format.serialize(current_config) == \
'''
{
    "get_marc_server_url": "some_url"
}
'''.strip()
    def test_deserialize(self):
        start_data = '''
{
    "get_marc_server_url": "some_url"
}
'''
        config_format = config.JSONConfigStrategy()
        config_data = config_format.deserialize(start_data)
        assert config_data.get_marc_server_url == "some_url"
