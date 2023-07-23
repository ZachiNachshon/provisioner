#!/usr/bin/env python3

from typing import Optional

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.checks import Checks

DUMMY_VERSION = "v1.0.0"


class FakeGitHub(Checks):

    __registered_get_latest_version: dict[str, str] = None
    __registered_download_release_binary: dict[str, str] = None

    __mocked_get_latest_version: dict[str, str] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.__registered_get_latest_version = {}
        self.__registered_download_release_binary = {}
        self.__mocked_get_latest_version = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeGitHub":
        github = FakeGitHub(dry_run=dry_run, verbose=verbose)
        github.get_latest_version_fn = lambda owner, repo: github._register_get_latest_version(owner, repo)
        github.download_release_binary_fn = (
            lambda owner, repo, version, binary_name, binary_folder_path: github._register_download_binary(
                owner, repo, version, binary_name, binary_folder_path
            )
        )
        return github

    @staticmethod
    def create(ctx: Context) -> "FakeGitHub":
        return FakeGitHub._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def _register_get_latest_version(self, owner: str, repo: str) -> str:
        key = self._create_get_latest_version_key(owner, repo)
        if key in self.__mocked_get_latest_version:
            print("===============")
            print("===============")
            print("===============")
            print(self.__mocked_get_latest_version[key])
            print(self.__mocked_get_latest_version[key])
            print(self.__mocked_get_latest_version[key])
            self.__registered_get_latest_version[key] = self.__mocked_get_latest_version[key]
        else:
            self.__registered_get_latest_version[key] = DUMMY_VERSION
        return self.__registered_get_latest_version[key]

    def assert_get_latest_version(self, owner: str, repo: str, version: Optional[str] = DUMMY_VERSION) -> None:
        key = self._create_get_latest_version_key(owner, repo)
        if key not in self.__registered_get_latest_version:
            raise FakeEnvironmentAssertionError(
                f"GitHub expected to download a version but it never requested. owner: {owner}, repo: {repo}, version: {version}"
            )
        else:
            tool_ver = self.__registered_get_latest_version[key]
            if version and tool_ver != version:
                raise FakeEnvironmentAssertionError(
                    f"GitHub expected to download specific version but it never requested. owner: {owner}, repo: {repo}\n"
                    + f"Actual version:\n{tool_ver}\n"
                    + f"Expected version:\n{version}"
                )

    def _register_download_binary(
        self, owner: str, repo: str, version: str, binary_name: str, binary_folder_path: str
    ) -> str:
        key = self._create_download_release_binary_key(owner, repo, version, binary_name, binary_folder_path)
        self.__registered_download_release_binary[key] = f"{binary_folder_path}/{binary_name}"
        return self.__registered_download_release_binary[key]

    def assert_download_binary(
        self, owner: str, repo: str, version: str, binary_name: str, binary_folder_path: str
    ) -> None:
        key = self._create_download_release_binary_key(owner, repo, version, binary_name, binary_folder_path)
        if key not in self.__registered_download_release_binary:
            raise FakeEnvironmentAssertionError(
                "GitHub expected to download a binary to a specific filepath but it never happened.\n"
                + f"Actual registered values:\n{self.__registered_download_release_binary.values()}\n"
                + f"Expected value:\n{binary_folder_path}/{binary_name}"
            )

    def mock_get_latest_version(self, owner: str, repo: str, version: str) -> "FakeGitHub":
        self.__mocked_get_latest_version[self._create_get_latest_version_key(owner, repo)] = version
        return self

    def _create_get_latest_version_key(self, owner: str, repo: str) -> str:
        return f"{owner}_{repo}"

    def _create_download_release_binary_key(
        self, owner: str, repo: str, version: str, binary_name: str, binary_folder_path: str
    ) -> str:
        return f"{owner}_{repo}_{version}_{binary_name}_{binary_folder_path}"
