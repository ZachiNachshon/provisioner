#!/usr/bin/env python3

import unittest

import typer
from provisioner.runner.ansible.ansible_runner import AnsibleHost
from provisioner.test_lib.assertions import Assertion
from typer.testing import CliRunner

from provisioner_features_lib.remote.typer_remote_opts import (
    TyperRemoteOpts,
)
from provisioner_features_lib.remote.typer_remote_opts_fakes import *

ARG_CLI_OVERRIDE_ENVIRONMENT = "test-environment"
ARG_CLI_OVERRIDE_NODE_USERNAME = "test-node-username"
ARG_CLI_OVERRIDE_NODE_PASSWORD = "test-node-password"
ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key-file-path"
ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE = "arg-test-ip-discovery-range"

CONFIG_CLI_OVERRIDE_IP_DISCOVERY_RANGE = "config-test-ip-discovery-range"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/remote/typer_remote_opts_test.py
#


class TyperRemoteOptsTestShould(unittest.TestCase):
    def test_set_typer_remote_opts_from_config_values(self) -> None:
        remote_cfg = TestDataRemoteOpts.create_fake_remote_cfg()
        remote_cfg.lan_scan.ip_discovery_range = CONFIG_CLI_OVERRIDE_IP_DISCOVERY_RANGE

        typer_remote = TyperRemoteOpts(remote_cfg)
        typer_callback = typer_remote.as_typer_callback()

        app = typer.Typer()
        app.command("test-remote-opts")(typer_callback)
        runner = CliRunner()
        runner.invoke(app)
        cli_opts = typer_remote.to_cli_opts()

        self.assertIsNotNone(cli_opts)
        self.assertEqual(cli_opts.ip_discovery_range, CONFIG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)

        Assertion.expect_equal_objects(
            self,
            obj1=cli_opts.ansible_hosts,
            obj2=[
                AnsibleHost(
                    host=TEST_DATA_SSH_HOSTNAME_1,
                    ip_address=TEST_DATA_SSH_IP_ADDRESS_1,
                    username=TEST_DATA_REMOTE_NODE_USERNAME_1,
                    password=TEST_DATA_REMOTE_NODE_PASSWORD_1,
                ),
                AnsibleHost(
                    host=TEST_DATA_SSH_HOSTNAME_2,
                    ip_address=TEST_DATA_SSH_IP_ADDRESS_2,
                    username=TEST_DATA_REMOTE_NODE_USERNAME_2,
                    ssh_private_key_file_path=TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_2,
                ),
            ],
        )

    def test_override_typer_remote_opts_from_cli_arguments(self) -> None:
        typer_remote = TyperRemoteOpts(TestDataRemoteOpts.create_fake_remote_cfg())
        typer_callback = typer_remote.as_typer_callback()
        typer_callback(ip_discovery_range=ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)

        cli_opts = typer_remote.to_cli_opts()

        self.assertIsNotNone(cli_opts)
        self.assertEqual(cli_opts.ip_discovery_range, ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)
