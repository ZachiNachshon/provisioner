#!/usr/bin/env python3

from typing import List

from provisioner.domain.serialize import SerializationBase

INTERNAL_CONFIG_TEST_DATA_FILE_PATH = "provisioner/test_data/internal_config.yaml"
USER_CONFIG_TEST_DATA_FILE_PATH = "provisioner/test_data/user_config.yaml"


class FakeConfigObj(SerializationBase):
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
            self.supported_os_arch = FakeConfigObj.SupportedOsArch(os_arch_list)

    def merge(self, other: "FakeConfigObj") -> SerializationBase:
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
