#!/usr/bin/env python3

import unittest

import click
from click.testing import CliRunner
from components.remote.cli_remote_opts import cli_remote_opts
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.entrypoint import EntryPoint

from components.remote.remote_opts_fakes import *
from components.runtime.runner.ansible.ansible_runner import AnsibleHost
from components.runtime.test_lib.assertions import Assertion

ARG_CLI_OVERRIDE_ENVIRONMENT = "test-environment"
ARG_CLI_OVERRIDE_NODE_USERNAME = "test-node-username"
ARG_CLI_OVERRIDE_NODE_PASSWORD = "test-node-password"
ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key-file-path"
ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE = "arg-test-ip-discovery-range"

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_shared/components/remote/remote_opts_test.py
#
class TyperRemoteOptsTestShould(unittest.TestCase):
    def test_set_remote_opts_defaults_from_config_values(self) -> None:
        remote_cfg = TestDataRemoteOpts.create_fake_remote_cfg()
        root_menu = EntryPoint.create_cli_menu()

        @root_menu.command()
        @cli_remote_opts(remote_config=remote_cfg)
        @cli_modifiers
        @click.pass_context
        def dummy(ctx: click.Context) -> None:
            """Dummy click command"""
            remote_opts = CliRemoteOpts.from_click_ctx(ctx)
            self.assertIsNotNone(remote_opts)

            Assertion.expect_equal_objects(
                self,
                obj1=remote_opts.ansible_hosts,
                obj2=[
                        AnsibleHost(
                            host=TEST_DATA_SSH_HOSTNAME_1,
                            ip_address=TEST_DATA_SSH_IP_ADDRESS_1,
                            username=TEST_DATA_REMOTE_NODE_USERNAME_1,
                            password=TEST_DATA_REMOTE_NODE_PASSWORD_1,
                            ssh_private_key_file_path="",
                        ),
                        AnsibleHost(
                            host=TEST_DATA_SSH_HOSTNAME_2,
                            ip_address=TEST_DATA_SSH_IP_ADDRESS_2,
                            username=TEST_DATA_REMOTE_NODE_USERNAME_2,
                            password="",
                            ssh_private_key_file_path=TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_2,
                        ),
                    ],
                )
            if ctx.invoked_subcommand is None:
                click.echo(ctx.get_help())
        
        assert CliRunner().invoke(dummy).exit_code == 0

        # Check the exit code to see if there was an issue
        # result = CliRunner().invoke(dummy)
        # if result.exit_code != 0:
        #     print(f"Command failed with exit code {result.exit_code}")
        #     print(f"Error output: {result.output}")
        # else:
        #     print(f"Command succeeded: {result.output}")


    def test_override_click_remote_opts_from_cli_arguments(self) -> None:
        remote_cfg = TestDataRemoteOpts.create_fake_remote_cfg()
        remote_cfg.lan_scan.ip_discovery_range = ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE

        root_menu = EntryPoint.create_cli_menu()

        @root_menu.command()
        @cli_remote_opts(remote_config=remote_cfg)
        @cli_modifiers
        @click.pass_context
        def dummy(ctx: click.Context) -> None:
            """Dummy click command"""
            remote_opts = CliRemoteOpts.from_click_ctx(ctx)
            self.assertIsNotNone(remote_opts)
            self.assertEqual(remote_opts.ip_discovery_range, ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)
            if ctx.invoked_subcommand is None:
                click.echo(ctx.get_help())
        
        assert CliRunner().invoke(dummy).exit_code == 0
        
        
        
