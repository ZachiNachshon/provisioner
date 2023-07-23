#!/usr/bin/env python3

import unittest

from python_core_lib.domain.serialize import SerializationBase

from provisioner_features_lib.anchor.typer_anchor_opts import (
    CliAnchorOpts,
    TyperAnchorOpts,
    TyperResolvedAnchorOpts,
)
from provisioner_features_lib.anchor.typer_anchor_opts_fakes import TestDataAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig

ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN = "test-override-git-access-token"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/anchor/typer_anchor_opts_test.py
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


class TyperAnchorOptsTestShould(unittest.TestCase):
    def load_fake_anchor_config(self):
        fake_anchor_config = TestDataAnchorOpts.create_fake_anchor_opts().anchor_config
        TyperAnchorOpts.load(fake_anchor_config)
        ConfigResolver.config = FakeTestConfig(remote=fake_anchor_config)

    def test_set_typer_anchor_opts_from_config_values(self) -> None:
        self.load_fake_anchor_config()

        # This is a simulation of typer triggering the remote_args_callback
        # DO NOT SET AUTH VARIABLES SINCE THOSE WOULD BE TREATED AS CLI ARGUMENTS OVERRIDES
        TyperResolvedAnchorOpts.create(git_access_token=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN)

        # Assert TyperResolvedAnchorOpts
        from provisioner_features_lib.anchor.typer_anchor_opts import (
            GLOBAL_TYPER_CLI_ANCHOR_OPTS,
        )

        self.assertEqual(
            GLOBAL_TYPER_CLI_ANCHOR_OPTS._github_access_token, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN
        )

        # Assert CliAnchorOpts
        cli_anchor_opts = CliAnchorOpts.maybe_get()
        self.assertIsNotNone(cli_anchor_opts)
        self.assertEqual(cli_anchor_opts.git_access_token, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN)

    def test_override_typer_anchor_opts_from_cli_arguments(self) -> None:
        self.load_fake_anchor_config()

        # This is a simulation of typer triggering the anchor_args_callback
        TyperResolvedAnchorOpts.create(git_access_token=ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

        # Assert TyperResolvedAnchorOpts
        from provisioner_features_lib.anchor.typer_anchor_opts import (
            GLOBAL_TYPER_CLI_ANCHOR_OPTS,
        )

        self.assertEqual(GLOBAL_TYPER_CLI_ANCHOR_OPTS._github_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

        # Assert CliAnchorOpts
        cli_anchor_opts = CliAnchorOpts.maybe_get()
        self.assertIsNotNone(cli_anchor_opts)
        self.assertEqual(cli_anchor_opts.git_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

    def test_override_typer_anchor_args_callback(self) -> None:
        self.load_fake_anchor_config()

        from provisioner_features_lib.anchor.typer_anchor_opts_callback import (
            anchor_args_callback,
        )

        anchor_args_callback(git_access_token=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN)

        from provisioner_features_lib.anchor.typer_anchor_opts import (
            GLOBAL_TYPER_CLI_ANCHOR_OPTS,
        )

        self.assertEqual(
            GLOBAL_TYPER_CLI_ANCHOR_OPTS._github_access_token, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN
        )
