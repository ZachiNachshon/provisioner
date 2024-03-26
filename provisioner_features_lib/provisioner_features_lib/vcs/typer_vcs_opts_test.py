#!/usr/bin/env python3

import unittest

import typer
from typer.testing import CliRunner

from provisioner_features_lib.vcs.typer_vcs_opts import TyperVersionControl
from provisioner_features_lib.vcs.typer_vcs_opts_fakes import TestDataVersionControlOpts

CONFIG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN = "config-test-override-git-access-token"
ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN = "arg-test-override-git-access-token"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/vcs/typer_vcs_opts_test.py
#


class TyperVersionControlOptsTestShould(unittest.TestCase):
    def test_set_typer_vcs_opts_from_config_values(self) -> None:
        vcs_cfg = TestDataVersionControlOpts.create_fake_vcs_cfg()
        vcs_cfg.github.git_access_token = CONFIG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN

        typer_vcs = TyperVersionControl(vcs_cfg)
        typer_callback = typer_vcs.as_typer_callback()

        app = typer.Typer()
        app.command("test-vcs-opts")(typer_callback)
        runner = CliRunner()
        runner.invoke(app)
        cli_opts = typer_vcs.to_cli_opts()

        self.assertIsNotNone(cli_opts)
        self.assertEqual(cli_opts.git_access_token, CONFIG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

    def test_override_typer_vcs_opts_from_cli_arguments(self) -> None:
        typer_vcs = TyperVersionControl(TestDataVersionControlOpts.create_fake_vcs_cfg())
        typer_callback = typer_vcs.as_typer_callback()
        typer_callback(git_access_token=ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)

        cli_opts = typer_vcs.to_cli_opts()

        self.assertIsNotNone(cli_opts)
        self.assertEqual(cli_opts.git_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)
