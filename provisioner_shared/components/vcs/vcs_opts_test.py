#!/usr/bin/env python3

import unittest

import click
from components.remote.cli_remote_opts import cli_remote_opts
from components.remote.remote_opts_fakes import TestDataRemoteOpts
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.entrypoint import EntryPoint
from components.runtime.test_lib.test_cli_runner import TestCliRunner
from components.vcs.cli_vcs_opts import cli_vcs_opts
from components.vcs.vcs_opts import CliVersionControlOpts
from components.vcs.vcs_opts_fakes import TestDataVersionControlOpts

ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN = "arg-test-override-git-access-token"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_shared/components/vcs/vcs_opts_test.py
#
class TyperVersionControlOptsTestShould(unittest.TestCase):

    def test_override_click_vcs_opts_from_cli_arguments(self) -> None:
        vcs_cfg = TestDataVersionControlOpts.create_fake_vcs_cfg()
        vcs_cfg.github.git_access_token = ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN

        root_menu = EntryPoint.create_cli_menu()

        @root_menu.command()
        @cli_vcs_opts(vcs_config=vcs_cfg)
        @cli_modifiers
        @click.pass_context
        def dummy(ctx: click.Context) -> None:
            """Dummy click command"""
            vcs_opts = CliVersionControlOpts.from_click_ctx(ctx)
            self.assertIsNotNone(vcs_opts)
            self.assertEqual(vcs_opts.git_access_token, ARG_CLI_OVERRIDE_GITHUB_ACCESS_TOKEN)
            if ctx.invoked_subcommand is None:
                click.echo(ctx.get_help())
        
        TestCliRunner.run(dummy)
