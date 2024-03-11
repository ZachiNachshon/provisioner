#!/usr/bin/env python3

import unittest

from provisioner.domain.serialize import SerializationBase

from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.vcs.typer_vcs_opts import (
    CliVersionControlOpts,
    TyperResolvedAnchorOpts,
    TyperVersionControlOpts,
)
from provisioner_features_lib.vcs.typer_vcs_opts_fakes import TestDataVersionControlOpts

ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN = "test-override-git-access-token"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/vcs/typer_vcs_opts_test.py
#


class FakeTestConfig(SerializationBase):

    remote: RemoteConfig = None

    def __init__(self, remote: RemoteConfig) -> None:
        super().__init__({})
        self.remote = remote

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self


class TyperVersionControlOptsTestShould(unittest.TestCase):
    def load_fake_vcs_config(self):
        fake_vcs_config = TestDataVersionControlOpts.create_fake_vcs_opts()._vcs_config
        TyperVersionControlOpts.load(fake_vcs_config)
        ConfigResolver.config = FakeTestConfig(remote=fake_vcs_config)

    def test_set_typer_vcs_opts_from_config_values(self) -> None:
        self.load_fake_vcs_config()

        # This is a simulation of typer triggering the remote_args_callback
        # DO NOT SET AUTH VARIABLES SINCE THOSE WOULD BE TREATED AS CLI ARGUMENTS OVERRIDES
        TyperResolvedAnchorOpts.create(git_access_token=TestDataVersionControlOpts.TEST_DATA_GITHUB_ACCESS_TOKEN)

        # Assert TyperResolvedAnchorOpts
        from provisioner_features_lib.vcs.typer_vcs_opts import (
            GLOBAL_TYPER_CLI_VCS_OPTS,
        )

        self.assertEqual(
            GLOBAL_TYPER_CLI_VCS_OPTS._github_access_token, TestDataVersionControlOpts.TEST_DATA_GITHUB_ACCESS_TOKEN
        )

        # Assert CliAnchorOpts
        cli_vcs_opts = CliVersionControlOpts.maybe_get()
        self.assertIsNotNone(cli_vcs_opts)
        self.assertEqual(cli_vcs_opts.git_access_token, TestDataVersionControlOpts.TEST_DATA_GITHUB_ACCESS_TOKEN)

    def test_override_typer_vcs_opts_from_cli_arguments(self) -> None:
        self.load_fake_vcs_config()

        # This is a simulation of typer triggering the vcs_args_callback
        TyperResolvedAnchorOpts.create(git_access_token=ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

        # Assert TyperResolvedAnchorOpts
        from provisioner_features_lib.vcs.typer_vcs_opts import (
            GLOBAL_TYPER_CLI_VCS_OPTS,
        )

        self.assertEqual(GLOBAL_TYPER_CLI_VCS_OPTS._github_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

        # Assert CliAnchorOpts
        cli_vcs_opts = CliVersionControlOpts.maybe_get()
        self.assertIsNotNone(cli_vcs_opts)
        self.assertEqual(cli_vcs_opts.git_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

    def test_override_typer_vcs_args_callback(self) -> None:
        self.load_fake_vcs_config()

        from provisioner_features_lib.vcs.typer_vcs_opts_callback import (
            vcs_args_callback,
        )

        vcs_args_callback(git_access_token=TestDataVersionControlOpts.TEST_DATA_GITHUB_ACCESS_TOKEN)

        from provisioner_features_lib.vcs.typer_vcs_opts import (
            GLOBAL_TYPER_CLI_VCS_OPTS,
        )

        self.assertEqual(
            GLOBAL_TYPER_CLI_VCS_OPTS._github_access_token, TestDataVersionControlOpts.TEST_DATA_GITHUB_ACCESS_TOKEN
        )
