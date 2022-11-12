#!/usr/bin/env python3

import unittest
from typing import List
from unittest import mock

from ..domain.serialize import SerializationBase
from ..errors.cli_errors import DownloadFileException, FailedToReadConfigurationFile
from ..infra.context import Context
from ..utils.io_utils import IOUtils
from ..utils.yaml_util import YamlUtil
from .config_reader import ConfigReader

INTERNAL_CONFIG_TEST_DATA_FILE_PATH = "python_scripts_lib/test_data/internal_config.yaml"
USER_CONFIG_TEST_DATA_FILE_PATH = "python_scripts_lib/test_data/user_config.yaml"


class FakeDomainObj(SerializationBase):
    """
    test_data:
    repo_url: https://github.com/org/repo.git
    branch_revs:
        master: a1s2d3f
    utilities:
        - kubectl
        - anchor
        - git-deps-syncer
    supported_os_arch:
        - linux:
            amd64: true
        - darwin:
            arm: false
    """

    class SupportedOsArch:
        linux: dict[str, bool] = None
        darwin: dict[str, bool] = None

        def __init__(self, list_obj) -> None:
            for os_arch in list_obj:
                if os_arch.get("linux") is not None:
                    self.linux = os_arch.get("linux")
                if os_arch.get("darwin") is not None:
                    self.darwin = os_arch.get("darwin")

    repo_url: str
    branch_revs: dict[str, str]
    utilities: List[str]
    supported_os_arch: SupportedOsArch = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        test_data = dict_obj["test_data"]
        if "repo_url" in test_data:
            self.repo_url = test_data["repo_url"]
        if "branch_revs" in test_data:
            self.branch_revs = test_data["branch_revs"]
        if "utilities" in test_data:
            self.utilities = test_data["utilities"]
        if "supported_os_arch" in test_data:
            os_arch_list = test_data["supported_os_arch"]
            self.supported_os_arch = FakeDomainObj.SupportedOsArch(os_arch_list)

    def merge(self, other: "FakeDomainObj") -> SerializationBase:
        other_test_data = other.dict_obj["test_data"]
        if "repo_url" in other_test_data:
            self.repo_url = other_test_data["repo_url"]

        if "branch_revs" in other_test_data:
            other_branch_revs = other_test_data["branch_revs"]
            if "master" in other_branch_revs:
                self.branch_revs["master"] = other_branch_revs["master"]

        if other_test_data["utilities"]:
            self.utilities = other_test_data["utilities"]

        if other.supported_os_arch:
            if other.supported_os_arch.linux:
                self.supported_os_arch.linux = other.supported_os_arch.linux
            if other.supported_os_arch.darwin:
                self.supported_os_arch.darwin = other.supported_os_arch.darwin

        return self


class ConfigReaderTestShould(unittest.TestCase):
    def test_read_only_internal_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        output: FakeDomainObj = config_reader.read_config_fn(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH, class_name=FakeDomainObj, user_path="/path/to/unkonwn"
        )

        self.assertEqual(output.repo_url, "https://github.com/internal-org/internal-repo.git")
        self.assertEqual(output.branch_revs["master"], "a1s2d3f")
        self.assertEqual(len(output.utilities), 3)
        self.assertEqual(output.utilities[0], "kubectl")
        self.assertEqual(output.utilities[1], "anchor")
        self.assertEqual(output.utilities[2], "git-deps-syncer")
        self.assertEqual(output.supported_os_arch.linux["amd64"], True)
        self.assertEqual(output.supported_os_arch.darwin["arm"], False)

    def test_fail_no_internal_config_files_found(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        with self.assertRaises(FileNotFoundError):
            output: FakeDomainObj = config_reader.read_config_fn(
                internal_path="/path/to/unknown", class_name=FakeDomainObj, user_path="/path/to/unknown"
            )

    def test_config_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        output: FakeDomainObj = config_reader.read_config_fn(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
            class_name=FakeDomainObj,
            user_path=USER_CONFIG_TEST_DATA_FILE_PATH,
        )

        self.assertEqual(output.repo_url, "https://github.com/user-org/user-repo.git")
        self.assertEqual(output.branch_revs["master"], "abcd123")
        self.assertEqual(len(output.utilities), 1)
        self.assertEqual(output.utilities[0], "anchor")
        self.assertNotIn("kubectl", output.utilities)
        self.assertNotIn("git-deps-syncer", output.utilities)
        self.assertEqual(output.supported_os_arch.linux["amd64"], False)
        self.assertEqual(output.supported_os_arch.darwin["arm"], False)

    def test_return_internal_config_when_no_user_config_path(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        output: FakeDomainObj = config_reader.read_config_fn(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH, class_name=FakeDomainObj
        )

        self.assertEqual(output.repo_url, "https://github.com/internal-org/internal-repo.git")
        self.assertEqual(len(output.utilities), 3)

    @mock.patch(
        "python_scripts_lib.config.config_reader_test.FakeDomainObj.merge",
        side_effect=Exception("test merge exception"),
    )
    def test_fail_to_merge_user_config(self, merge_config_call: mock.MagicMock):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        with self.assertRaises(FailedToReadConfigurationFile):
            output: FakeDomainObj = config_reader.read_config_fn(
                internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
                class_name=FakeDomainObj,
                user_path=USER_CONFIG_TEST_DATA_FILE_PATH,
            )
