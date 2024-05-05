#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner.config.manager.config_manager import ConfigManager
from provisioner.domain.serialize import SerializationBase
from provisioner.errors.cli_errors import FailedToMergeConfiguration
from provisioner.test_data.domain import (
    INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
    USER_CONFIG_TEST_DATA_FILE_PATH,
    FakeConfigObj,
)
from provisioner.test_lib.assertions import Assertion

ARG_CONFIG_INTERNAL_PATH = "/path/to/internal/config"
ARG_CONFIG_USER_PATH = "/path/to/user/config"

ARG_PLUGIN_CONFIG_INTERNAL_PATH = "/path/to/internal/plugin/config"
ARG_PLUGIN_CONFIG_USER_PATH = "/path/to/user/plugin/config"

TEST_PLUGIN_NAME = "test_plugin"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner/config/manager/config_manager_test.py
#
class FakeBasicConfigObj(SerializationBase):

    string_value: str = None
    int_value: int = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "string_value" in dict_obj:
            self.string_value = dict_obj["string_value"]
        if "int_value" in dict_obj:
            self.int_value = dict_obj["int_value"]

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        if other.string_value:
            self.string_value = other.string_value
        if other.int_value:
            self.int_value = other.int_value
        return self


class FakeBasicPluginConfigObj(SerializationBase):

    url: str = None
    description: str = None
    int_value: int = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "url" in dict_obj:
            self.url = dict_obj["url"]
        if "description" in dict_obj:
            self.description = dict_obj["description"]
        if "int_value" in dict_obj:
            self.int_value = dict_obj["int_value"]

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        if other.url:
            self.url = other.url
        if other.description:
            self.description = other.description
        if other.int_value:
            self.int_value = other.int_value
        return self


class ConfigResolverTestShould(unittest.TestCase):
    def setUp(self) -> None:
        ConfigManager.instance().nullify()

    @staticmethod
    def create_fake_config_obj():
        return FakeBasicConfigObj(
            {
                "string_value": "fake_string",
                "int_value": 123,
            }
        )

    @staticmethod
    def create_fake_config_dict():
        return {
            "string_value": "user_string",
            "int_value": 123,
        }

    @staticmethod
    def create_plugins_fake_config_obj():
        return FakeBasicPluginConfigObj(
            {
                "url": "http://plugin.com",
                "description": "awesome plugin",
                "int_value": 123,
            }
        )

    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_fake_config_obj()],
    )
    def test_load_provisioner_config_from_internal_only(self, run_call: mock.MagicMock) -> None:
        ConfigManager.instance().load(internal_path=ARG_CONFIG_INTERNAL_PATH, user_path=None, cls=FakeBasicConfigObj)
        resolved_config: FakeBasicConfigObj = ConfigManager.instance().get_config()
        Assertion.expect_equal_objects(self, resolved_config.string_value, "fake_string")
        Assertion.expect_equal_objects(self, resolved_config.int_value, 123)

    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_as_json_dict_safe_fn",
        side_effect=[create_fake_config_dict()],
    )
    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_fake_config_obj()],
    )
    def test_load_provisioner_config_from_internal_and_user(
        self, read_cfg_call: mock.MagicMock, read_dict_call: mock.MagicMock
    ) -> None:

        ConfigManager.instance().load(
            internal_path=ARG_CONFIG_INTERNAL_PATH, user_path=ARG_CONFIG_USER_PATH, cls=FakeBasicConfigObj
        )
        resolved_config: FakeBasicConfigObj = ConfigManager.instance().get_config()
        Assertion.expect_equal_objects(self, resolved_config.string_value, "user_string")
        Assertion.expect_equal_objects(self, resolved_config.int_value, 123)

    def test_load_provisioner_config_and_merge_with_user_config(self):
        ConfigManager.instance().load(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
            user_path=USER_CONFIG_TEST_DATA_FILE_PATH,
            cls=FakeConfigObj,
        )
        output: FakeConfigObj = ConfigManager.instance().get_config()
        self.assertEqual(output.repo_url, "https://github.com/user-org/user-repo.git")
        self.assertEqual(output.branch_revs["master"], "abcd123")
        self.assertEqual(len(output.utilities), 1)
        self.assertEqual(output.utilities[0], "anchor")
        self.assertNotIn("kubectl", output.utilities)
        self.assertNotIn("git-deps-syncer", output.utilities)
        self.assertEqual(output.supported_os_arch.linux["amd64"], False)
        self.assertEqual(output.supported_os_arch.darwin["arm"], False)

    @mock.patch(
        "provisioner.config.manager.config_manager.ConfigManager._merge_user_config_with_internal", return_value=None
    )
    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_as_json_dict_safe_fn",
        side_effect=[create_fake_config_dict()],
    )
    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_fake_config_obj()],
    )
    def test_fail_to_merge_user_config(
        self, read_cfg_call: mock.MagicMock, read_dict_call: mock.MagicMock, merge_call: mock.MagicMock
    ) -> None:

        with self.assertRaises(FailedToMergeConfiguration):
            ConfigManager.instance().load(
                internal_path=ARG_CONFIG_INTERNAL_PATH, user_path=ARG_CONFIG_USER_PATH, cls=FakeBasicConfigObj
            )

    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_fake_config_obj()],
    )
    def test_no_user_plugin_config(self, read_cfg_call: mock.MagicMock) -> None:
        ConfigManager.instance().config = self.create_fake_config_obj()
        ConfigManager.instance().load_plugin_config(
            plugin_name=TEST_PLUGIN_NAME, internal_path=ARG_PLUGIN_CONFIG_INTERNAL_PATH, cls=FakeBasicConfigObj
        )
        output = ConfigManager.instance().get_config()
        self.assertIsNotNone(output.dict_obj["plugins"][TEST_PLUGIN_NAME])
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].dict_obj["string_value"], "fake_string")
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].dict_obj["int_value"], 123)

    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_plugins_fake_config_obj()],
    )
    def test_empty_user_plugin_config(self, read_cfg_call: mock.MagicMock) -> None:
        ConfigManager.instance().config = self.create_plugins_fake_config_obj()
        ConfigManager.instance()._user_config_raw_dict = {"plugins": {}}
        ConfigManager.instance().load_plugin_config(
            plugin_name=TEST_PLUGIN_NAME, internal_path=ARG_PLUGIN_CONFIG_INTERNAL_PATH, cls=FakeBasicPluginConfigObj
        )
        output = ConfigManager.instance().get_config()
        self.assertIsNotNone(output.dict_obj["plugins"][TEST_PLUGIN_NAME])
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].url, "http://plugin.com")
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].description, "awesome plugin")
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].int_value, 123)

    @mock.patch(
        "provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn",
        side_effect=[create_plugins_fake_config_obj()],
    )
    def test_merge_plugin_config_success(self, read_cfg_call: mock.MagicMock) -> None:
        ConfigManager.instance().config = self.create_plugins_fake_config_obj()
        ConfigManager.instance()._user_config_raw_dict = {
            "plugins": {
                TEST_PLUGIN_NAME: {"url": "http://user-plugin.com", "description": "user plugin", "int_value": 456}
            }
        }

        ConfigManager.instance().load_plugin_config(
            plugin_name=TEST_PLUGIN_NAME,
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
            cls=FakeBasicPluginConfigObj,
        )
        output = ConfigManager.instance().get_config()
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].url, "http://user-plugin.com")
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].description, "user plugin")
        self.assertEqual(output.dict_obj["plugins"][TEST_PLUGIN_NAME].int_value, 456)
