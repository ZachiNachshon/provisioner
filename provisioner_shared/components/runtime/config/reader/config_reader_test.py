#!/usr/bin/env python3

import unittest

from provisioner_shared.components.runtime.config.reader.config_reader import ConfigReader
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.test_data.domain import INTERNAL_CONFIG_TEST_DATA_FILE_PATH, FakeConfigObj
from provisioner_shared.components.runtime.utils.io_utils import IOUtils
from provisioner_shared.components.runtime.utils.yaml_util import YamlUtil

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner/config/reader/config_reader_test.py
#


class ConfigReaderTestShould(unittest.TestCase):
    def test_read_only_internal_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        output: FakeConfigObj = config_reader.read_config_fn(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH,
            cls=FakeConfigObj,
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
            config_reader.read_config_fn(
                internal_path="/path/to/unknown",
                cls=FakeConfigObj,
            )

    def test_return_internal_config_when_no_user_config_path(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx, IOUtils.create(ctx))
        config_reader = ConfigReader.create(yaml_util)

        output: FakeConfigObj = config_reader.read_config_fn(
            internal_path=INTERNAL_CONFIG_TEST_DATA_FILE_PATH, cls=FakeConfigObj
        )

        self.assertEqual(output.repo_url, "https://github.com/internal-org/internal-repo.git")
        self.assertEqual(len(output.utilities), 3)
