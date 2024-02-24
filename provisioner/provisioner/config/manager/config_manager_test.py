#!/usr/bin/env python3

import unittest
from unittest import SkipTest, mock
from click import Context
from provisioner.config.manager.config_manager import ConfigManager
from provisioner.config.reader.config_reader import ConfigReader

from provisioner.domain.serialize import SerializationBase
from provisioner.errors.cli_errors import FailedToReadConfigurationFile
from provisioner.test_data.domain import INTERNAL_CONFIG_TEST_DATA_FILE_PATH, USER_CONFIG_TEST_DATA_FILE_PATH, FakeConfigObj
from provisioner.test_lib.assertions import Assertion
from provisioner.utils.io_utils import IOUtils
from provisioner.utils.yaml_util import YamlUtil

ARG_CONFIG_INTERNAL_PATH = "/path/to/internal/config"
ARG_CONFIG_USER_PATH = "/path/to/user/config"

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
        if "string_value" in other.dict_obj:
            self.string_value = other.dict_obj["string_value"]
        if "int_value" in other.dict_obj:
            self.int_value = other.dict_obj["int_value"]
        return self

class ConfigResolverTestShould(unittest.TestCase):

    def setUp(self) -> None:
        print("Setting up...")
        ConfigManager.instance().config = None

    @staticmethod
    def create_fake_config_obj():
        return FakeBasicConfigObj({
            "string_value": "fake_string",
            "int_value": 123,
        })

    @staticmethod
    def create_fake_config_dict():
        return {
            "string_value": "user_string",
            "int_value": 123,
        }

    @mock.patch("provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn", side_effect=[create_fake_config_obj()])
    def test_load_provisioner_config_from_internal_only(self, run_call: mock.MagicMock) -> None:
        ConfigManager.instance().load(
            internal_path=ARG_CONFIG_INTERNAL_PATH, 
            user_path=None, 
            cls=FakeBasicConfigObj
        )
        resolved_config = ConfigManager.instance().get_config()
        Assertion.expect_equal_objects(self, resolved_config.string_value, "fake_string")
        Assertion.expect_equal_objects(self, resolved_config.int_value, 123)

    # @mock.patch("provisioner.config.reader.config_reader.ConfigReader.read_config_as_json_dict_fn", side_effect=[create_fake_config_dict()])
    # @mock.patch("provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn", side_effect=[create_fake_config_obj()])
    # def test_load_provisioner_config_from_internal_and_user(
    #     self, 
    #     read_cfg_call: mock.MagicMock, 
    #     read_dict_call: mock.MagicMock) -> None:

    #     ConfigManager.instance().load(
    #         internal_path=ARG_CONFIG_INTERNAL_PATH, 
    #         user_path=ARG_CONFIG_USER_PATH, 
    #         cls=FakeBasicConfigObj
    #     )
    #     resolved_config = ConfigManager.instance().get_config()
    #     Assertion.expect_equal_objects(self, resolved_config.string_value, "user_string")
    #     Assertion.expect_equal_objects(self, resolved_config.int_value, 123)

    def test_load_provisioner_config_and_merge_with_user_config(self):
        ConfigManager.instance().load(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH, 
            user_path=USER_CONFIG_TEST_DATA_FILE_PATH, 
            cls=FakeConfigObj
        )
        output = ConfigManager.instance().get_config()
        self.assertEqual(output.repo_url, "https://github.com/user-org/user-repo.git")
        self.assertEqual(output.branch_revs["master"], "abcd123")
        self.assertEqual(len(output.utilities), 1)
        self.assertEqual(output.utilities[0], "anchor")
        self.assertNotIn("kubectl", output.utilities)
        self.assertNotIn("git-deps-syncer", output.utilities)
        self.assertEqual(output.supported_os_arch.linux["amd64"], False)
        self.assertEqual(output.supported_os_arch.darwin["arm"], False)
        
    #     @mock.patch(
    #     "provisioner.config.reader.config_reader_test.FakeDomainObj.merge",
    #     side_effect=Exception("test merge exception"),
    # )
        
    @mock.patch("provisioner.config.manager.config_manager.ConfigManager._merge_user_config_with_internal", return_value=None)
    @mock.patch("provisioner.config.reader.config_reader.ConfigReader.read_config_as_json_dict_fn", side_effect=[create_fake_config_dict()])
    @mock.patch("provisioner.config.reader.config_reader.ConfigReader.read_config_safe_fn", side_effect=[create_fake_config_obj()])
    def test_fail_to_merge_user_config(
        self, 
        read_cfg_call: mock.MagicMock, 
        read_dict_call: mock.MagicMock,
        merge_call: mock.MagicMock) -> None:

        with self.assertRaises(FailedToReadConfigurationFile):
            ConfigManager.instance().load(
                internal_path=ARG_CONFIG_INTERNAL_PATH, 
                user_path=ARG_CONFIG_USER_PATH,
                cls=FakeBasicConfigObj
        )