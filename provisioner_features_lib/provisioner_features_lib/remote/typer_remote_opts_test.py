#!/usr/bin/env python3

import unittest

from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.runner.ansible.ansible_runner import AnsibleHost
from python_core_lib.test_lib.assertions import Assertion

from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import (
    CliRemoteOpts,
    TyperRemoteOpts,
    TyperResolvedRemoteOpts,
)
from provisioner_features_lib.remote.typer_remote_opts_fakes import *

ARG_CLI_OVERRIDE_ENVIRONMENT = "test-environment"
ARG_CLI_OVERRIDE_NODE_USERNAME = "test-node-username"
ARG_CLI_OVERRIDE_NODE_PASSWORD = "test-node-password"
ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key-file-path"
ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE = "test-ip-discovery-range"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/remote/typer_remote_opts_test.py
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


class TyperRemoteOptsTestShould(unittest.TestCase):
    def load_fake_remote_config(self):
        fake_remote_config = TestDataRemoteOpts.create_fake_remote_opts().remote_config
        TyperRemoteOpts.load(fake_remote_config)
        ConfigResolver.config = FakeTestConfig(remote=fake_remote_config)

    def test_set_typer_remote_opts_from_config_values(self) -> None:
        self.load_fake_remote_config()

        # This is a simulation of typer triggering the remote_args_callback
        # DO NOT SET AUTH VARIABLES SINCE THOSE WOULD BE TREATED AS CLI ARGUMENTS OVERRIDES
        TyperResolvedRemoteOpts.create(
            environment=TEST_DATA_ENVIRONMENT,
            remote_hosts=TEST_REMOTE_HOSTS_DICT,
        )

        # Assert TyperResolvedRemoteOpts
        from provisioner_features_lib.remote.typer_remote_opts import (
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS,
        )

        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._environment, TEST_DATA_ENVIRONMENT)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._remote_hosts, TEST_REMOTE_HOSTS_DICT)

        # Assert CliRemoteOpts
        cli_remote_opts = CliRemoteOpts.maybe_get()
        self.assertIsNotNone(cli_remote_opts)
        self.assertEqual(cli_remote_opts.environment, TEST_DATA_ENVIRONMENT)

        Assertion.expect_equal_objects(
            self,
            obj1=cli_remote_opts.ansible_hosts,
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
        self.load_fake_remote_config()

        # This is a simulation of typer triggering the remote_args_callback
        TyperResolvedRemoteOpts.create(
            ARG_CLI_OVERRIDE_ENVIRONMENT,
            ARG_CLI_OVERRIDE_NODE_USERNAME,
            ARG_CLI_OVERRIDE_NODE_PASSWORD,
            ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH,
            ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE,
            TEST_REMOTE_HOSTS_DICT,
        )

        # Assert TyperResolvedRemoteOpts
        from provisioner_features_lib.remote.typer_remote_opts import (
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS,
        )

        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._environment, ARG_CLI_OVERRIDE_ENVIRONMENT)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_username, ARG_CLI_OVERRIDE_NODE_USERNAME)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_password, ARG_CLI_OVERRIDE_NODE_PASSWORD)
        self.assertEqual(
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ssh_private_key_file_path, ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH
        )
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ip_discovery_range, ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._remote_hosts, TEST_REMOTE_HOSTS_DICT)

        # Assert CliRemoteOpts
        cli_remote_opts = CliRemoteOpts.maybe_get()
        self.assertIsNotNone(cli_remote_opts)
        self.assertEqual(cli_remote_opts.environment, ARG_CLI_OVERRIDE_ENVIRONMENT)
        self.assertEqual(cli_remote_opts.node_username, ARG_CLI_OVERRIDE_NODE_USERNAME)
        self.assertEqual(cli_remote_opts.node_password, ARG_CLI_OVERRIDE_NODE_PASSWORD)
        self.assertEqual(cli_remote_opts.ssh_private_key_file_path, ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH)
        self.assertEqual(cli_remote_opts.ip_discovery_range, ARG_CLI_OVERRIDE_IP_DISCOVERY_RANGE)

        Assertion.expect_equal_objects(
            self,
            obj1=cli_remote_opts.ansible_hosts,
            obj2=[
                AnsibleHost(
                    host=TEST_DATA_SSH_HOSTNAME_1,
                    ip_address=TEST_DATA_SSH_IP_ADDRESS_1,
                    username=ARG_CLI_OVERRIDE_NODE_USERNAME,
                    password=ARG_CLI_OVERRIDE_NODE_PASSWORD,
                    ssh_private_key_file_path=ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH,
                ),
                AnsibleHost(
                    host=TEST_DATA_SSH_HOSTNAME_2,
                    ip_address=TEST_DATA_SSH_IP_ADDRESS_2,
                    username=ARG_CLI_OVERRIDE_NODE_USERNAME,
                    password=ARG_CLI_OVERRIDE_NODE_PASSWORD,
                    ssh_private_key_file_path=ARG_CLI_OVERRIDE_SSH_PRIVATE_KEY_FILE_PATH,
                ),
            ],
        )

    def test_override_typer_remote_args_callback(self) -> None:
        self.load_fake_remote_config()
        from provisioner_features_lib.remote.typer_remote_opts_callback import (
            remote_args_callback,
        )

        remote_args_callback(
            environment=TEST_DATA_ENVIRONMENT,
            node_username=TEST_DATA_REMOTE_NODE_USERNAME_1,
            node_password=TEST_DATA_REMOTE_NODE_PASSWORD_1,
            ssh_private_key_file_path=TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1,
            ip_discovery_range=TEST_DATA_REMOTE_IP_DISCOVERY_RANGE,
        )

        from provisioner_features_lib.remote.typer_remote_opts import (
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS,
        )

        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._environment, TEST_DATA_ENVIRONMENT)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_username, TEST_DATA_REMOTE_NODE_USERNAME_1)
        self.assertEqual(GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_password, TEST_DATA_REMOTE_NODE_PASSWORD_1)
        self.assertEqual(
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ssh_private_key_file_path,
            TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1,
        )
        self.assertEqual(
            GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ip_discovery_range,
            TEST_DATA_REMOTE_IP_DISCOVERY_RANGE,
        )
