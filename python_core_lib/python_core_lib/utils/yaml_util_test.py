#!/usr/bin/env python3

import unittest
from typing import List

from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.infra.context import Context
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.yaml_util import YamlUtil

YAML_TEST_DATA_FILE_PATH = "python_core_lib/test_data/internal_config.yaml"


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

    repo_url: str
    branch_revs: dict[str, str]
    utilities: List[str]
    supported_os_arch: List[dict[str, str]]

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
            self.supported_os_arch = test_data["supported_os_arch"]


class YamlUtilTestShould(unittest.TestCase):
    def test_read_yaml_file_successfully(self):
        ctx = Context.create()
        reader = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        output = reader.read_file_fn(file_path=YAML_TEST_DATA_FILE_PATH, class_name=FakeDomainObj)
        self.assertEqual(output.repo_url, "https://github.com/internal-org/internal-repo.git")
        self.assertEqual(output.branch_revs["master"], "a1s2d3f")
        self.assertEqual(len(output.utilities), 3)
        self.assertEqual(output.utilities[0], "kubectl")
        self.assertEqual(output.utilities[1], "anchor")
        self.assertEqual(output.utilities[2], "git-deps-syncer")
        self.assertEqual(output.supported_os_arch[0]["linux"]["amd64"], True)
        self.assertEqual(output.supported_os_arch[1]["darwin"]["arm"], False)

    def test_read_yaml_fail(self):
        ctx = Context.create()
        reader = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        with self.assertRaises(FileNotFoundError):
            reader.read_file_fn(file_path="/path/to/unknown", class_name=FakeDomainObj)
