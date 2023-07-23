#!/usr/bin/env python3

import copy
import unittest
from unittest import mock

from python_core_lib.runner.ansible.ansible_runner import AnsibleHost
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    NetworkDeviceAuthenticationMethod,
    NetworkDeviceSelectionMethod,
    RemoteMachineConnector,
)
from provisioner_features_lib.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import (
    TEST_DATA_REMOTE_NODE_PASSWORD_1,
    TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1,
    TestDataRemoteOpts,
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/remote/remote_connector_test.py
#
ARG_IP_DISCOVERY_RANGE = "1.1.1.1/24"
DRY_RUN_RESPONSE = "DRY_RUN_RESPONSE"

COLLECT_AUTH_CUSTOM_USERNAME = "collect-ssh-info-test-user"
COLLECT_AUTH_CUSTOM_PASSWORD = "collect-ssh-info-test-pass"
COLLECT_AUTH_CUSTOM_SSH_PRIVATE_KEY = "collect-ssh-info-test-ssh-private-key"

HOST_SELECTION_HOST_ID_1 = (
    f"{TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}, {TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1}"
)
HOST_SELECTION_HOST_ID_2 = (
    f"{TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_2}, {TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_2}"
)
HOST_SELECTION_OPTIONS_LIST = [HOST_SELECTION_HOST_ID_1, HOST_SELECTION_HOST_ID_2]

HOST_SELECTION_OPTIONS_DICT = {
    HOST_SELECTION_HOST_ID_1: {
        "hostname": TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
        "ip_address": TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1,
    },
    HOST_SELECTION_HOST_ID_2: {
        "hostname": TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_2,
        "ip_address": TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_2,
    },
}

REMOTE_MACHINE_CONNECTOR_PATH = "provisioner_features_lib.remote.remote_connector.RemoteMachineConnector"


class RemoteMachineConnectorTestShould(unittest.TestCase):
    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_selection_method",
        side_effect=[NetworkDeviceSelectionMethod.UserConfig],
    )
    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._run_config_based_host_selection",
        side_effect=[TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS],
    )
    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._collect_ssh_auth_info")
    def test_collect_ssh_connection_info_from_config(
        self,
        collect_auth_info_call: mock.MagicMock,
        host_selection_call: mock.MagicMock,
        device_selection_call: mock.MagicMock,
    ) -> None:

        env = TestEnv.create()
        RemoteMachineConnector(env.get_collaborators()).collect_ssh_connection_info(
            env.get_context(), CliRemoteOpts(), force_single_conn_info=True
        )
        Assertion.expect_call_argument(self, host_selection_call, "force_single_conn_info", True)
        Assertion.expect_call_argument(
            self, collect_auth_info_call, "ansible_hosts", TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS
        )

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_selection_method",
        side_effect=[NetworkDeviceSelectionMethod.ScanLAN],
    )
    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._run_scan_lan_host_selection",
        side_effect=[TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS],
    )
    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._collect_ssh_auth_info")
    def test_collect_ssh_connection_info_from_lan_scan(
        self,
        collect_auth_info_call: mock.MagicMock,
        host_selection_call: mock.MagicMock,
        device_selection_call: mock.MagicMock,
    ) -> None:

        env = TestEnv.create()
        RemoteMachineConnector(env.get_collaborators()).collect_ssh_connection_info(
            env.get_context(), CliRemoteOpts(), force_single_conn_info=True
        )
        Assertion.expect_call_argument(self, host_selection_call, "force_single_conn_info", True)
        Assertion.expect_call_argument(
            self, collect_auth_info_call, "ansible_hosts", TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS
        )

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_selection_method",
        side_effect=[NetworkDeviceSelectionMethod.UserPrompt],
    )
    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._run_manual_host_selection",
        side_effect=[TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS],
    )
    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._collect_ssh_auth_info")
    def test_collect_ssh_connection_info_from_manual_input(
        self,
        collect_auth_info_call: mock.MagicMock,
        host_selection_call: mock.MagicMock,
        device_selection_call: mock.MagicMock,
    ) -> None:

        env = TestEnv.create()
        RemoteMachineConnector(env.get_collaborators()).collect_ssh_connection_info(env.get_context(), CliRemoteOpts())
        Assertion.expect_call_argument(
            self, collect_auth_info_call, "ansible_hosts", TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS
        )

    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_selection_method", side_effect=[None])
    def test_collect_ssh_connection_info_failed_on_missing_selection_method(
        self, device_selection_call: mock.MagicMock
    ) -> None:
        env = TestEnv.create()
        response = RemoteMachineConnector(env.get_collaborators()).collect_ssh_connection_info(
            env.get_context(), CliRemoteOpts()
        )
        self.assertIsNone(response)

    def test_collect_dhcpcd_configuration_info(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter a desired remote static IP address (example: 192.168.1.2XX)",
            TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
        )
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter the gateway address", TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS
        )
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter the DNS resolver address", TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS
        )

        response = RemoteMachineConnector(env.get_collaborators()).collect_dhcpcd_configuration_info(
            env.get_context(), TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS
        )

        Assertion.expect_equal_objects(
            self,
            response,
            DHCPCDConfigurationInfo(
                TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS,
                TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS,
                TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
            ),
        )

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_authentication_method",
        return_value=NetworkDeviceAuthenticationMethod.Password,
    )
    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._collect_auth_password", return_value=COLLECT_AUTH_CUSTOM_PASSWORD)
    def test_collect_ssh_auth_info_password(
        self, collect_auth_pass_call: mock.MagicMock, device_auth_method_call: mock.MagicMock
    ) -> None:

        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter remote node user name", COLLECT_AUTH_CUSTOM_USERNAME
        )
        # Ansible hosts are being changed within the test method, we deep copy to avoid from interfering with other tests
        ansible_hosts_deep_copy = copy.deepcopy(TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS)

        response = RemoteMachineConnector(env.get_collaborators())._collect_ssh_auth_info(
            env.get_context(), CliRemoteOpts(), ansible_hosts_deep_copy
        )

        self.assertEqual(response.ansible_hosts[0].username, COLLECT_AUTH_CUSTOM_USERNAME)
        self.assertEqual(response.ansible_hosts[0].password, COLLECT_AUTH_CUSTOM_PASSWORD)
        self.assertEqual(response.ansible_hosts[1].username, COLLECT_AUTH_CUSTOM_USERNAME)
        self.assertEqual(response.ansible_hosts[1].password, COLLECT_AUTH_CUSTOM_PASSWORD)

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_authentication_method",
        return_value=NetworkDeviceAuthenticationMethod.SSHPrivateKeyPath,
    )
    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._collect_auth_ssh_private_key_path",
        return_value=COLLECT_AUTH_CUSTOM_SSH_PRIVATE_KEY,
    )
    def test_collect_ssh_auth_info_ssh_private_key(
        self, collect_auth_pass_call: mock.MagicMock, device_auth_method_call: mock.MagicMock
    ) -> None:

        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter remote node user name", COLLECT_AUTH_CUSTOM_USERNAME
        )
        # Ansible hosts are being changed within the test method, we deep copy to avoid from interfering with other tests
        ansible_hosts_deep_copy = copy.deepcopy(TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS)

        response = RemoteMachineConnector(env.get_collaborators())._collect_ssh_auth_info(
            env.get_context(), CliRemoteOpts(), ansible_hosts_deep_copy
        )

        self.assertEqual(response.ansible_hosts[0].username, COLLECT_AUTH_CUSTOM_USERNAME)
        self.assertEqual(response.ansible_hosts[0].ssh_private_key_file_path, COLLECT_AUTH_CUSTOM_SSH_PRIVATE_KEY)
        self.assertEqual(response.ansible_hosts[1].username, COLLECT_AUTH_CUSTOM_USERNAME)
        self.assertEqual(response.ansible_hosts[1].ssh_private_key_file_path, COLLECT_AUTH_CUSTOM_SSH_PRIVATE_KEY)

    # def test_collect_ssh_connection_info_dry_run_response(self) -> None:
    #     env = TestEnv.create(dry_run=True)
    #     response = RemoteMachineConnector(env.get_collaborators()).collect_ssh_connection_info(
    #         env.get_context(), CliRemoteOpts())
    #     self.assertEqual(response.ansible_hosts[0].host, DRY_RUN_RESPONSE)
    #     self.assertEqual(response.ansible_hosts[0].ip_address, DRY_RUN_RESPONSE)
    #     self.assertEqual(response.ansible_hosts[0].username, DRY_RUN_RESPONSE)
    #     self.assertEqual(response.ansible_hosts[0].password, DRY_RUN_RESPONSE)
    #     self.assertEqual(response.ansible_hosts[0].ssh_private_key_file_path, DRY_RUN_RESPONSE)

    def test_ask_for_network_device_selection_method(self) -> None:
        env = TestEnv.create()

        env.get_collaborators().prompter().mock_user_single_selection_response(
            prompt_str="Please choose network device selection method", response="Scan LAN"
        )

        response = RemoteMachineConnector(env.get_collaborators())._ask_for_network_device_selection_method()
        self.assertEqual(response, NetworkDeviceSelectionMethod.ScanLAN)

    def test_ask_for_network_device_authentication_method(self) -> None:
        env = TestEnv.create()

        env.get_collaborators().prompter().mock_user_single_selection_response(
            prompt_str="Please choose network device authentication method", response="SSH Private Key"
        )

        response = RemoteMachineConnector(env.get_collaborators())._ask_for_network_device_authentication_method()
        self.assertEqual(response, NetworkDeviceAuthenticationMethod.SSHPrivateKeyPath)

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._run_lan_scan_host_selection",
        side_effect=[TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS],
    )
    def test_run_host_ip_address_scan(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_yes_no_response("Scan LAN network for IP addresses at range", True)

        response = RemoteMachineConnector(env.get_collaborators())._run_scan_lan_host_selection(
            ARG_IP_DISCOVERY_RANGE, force_single_conn_info=False
        )
        Assertion.expect_equal_objects(self, response, TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS)
        Assertion.expect_call_argument(
            self, run_call, arg_name="ip_discovery_range", expected_value=ARG_IP_DISCOVERY_RANGE
        )

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}._ask_for_network_device_authentication_method",
        side_effect=[NetworkDeviceAuthenticationMethod.Password],
    )
    def test_run_manual_host_selection_success(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter remote node IP address", TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1
        )
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter remote node host name", TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1
        )

        response = RemoteMachineConnector(env.get_collaborators())._run_manual_host_selection(env.get_context())
        Assertion.expect_equal_objects(
            self,
            response,
            [
                AnsibleHost(
                    host=TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
                    ip_address=TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1,
                )
            ],
        )

    def test_collect_auth_password_from_cli_args(self) -> None:
        env = TestEnv.create()
        response = RemoteMachineConnector(env.get_collaborators())._collect_auth_password(
            env.get_context(), TestDataRemoteOpts.create_fake_cli_remote_opts()
        )
        self.assertEqual(response, TEST_DATA_REMOTE_NODE_PASSWORD_1)
        env.get_collaborators().printer().assert_output("Identified SSH password from CLI argument.")

    def test_collect_auth_password_from_user_prompt(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter remote node password", TestDataRemoteConnector.TEST_DATA_SSH_PASSWORD_1
        )
        response = RemoteMachineConnector(env.get_collaborators())._collect_auth_password(
            env.get_context(), CliRemoteOpts()
        )
        self.assertEqual(response, TestDataRemoteConnector.TEST_DATA_SSH_PASSWORD_1)

    def test_collect_auth_ssh_private_key_path_from_cli_args(self) -> None:
        env = TestEnv.create()
        response = RemoteMachineConnector(env.get_collaborators())._collect_auth_ssh_private_key_path(
            env.get_context(), TestDataRemoteOpts.create_fake_cli_remote_opts()
        )
        self.assertEqual(response, TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1)
        env.get_collaborators().printer().assert_output("Identified SSH private key path from CLI argument.")

    def test_collect_auth_ssh_private_key_path_from_user_prompt(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_input_response(
            "Enter SSH private key path", TestDataRemoteConnector.TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1
        )
        response = RemoteMachineConnector(env.get_collaborators())._collect_auth_ssh_private_key_path(
            env.get_context(), CliRemoteOpts()
        )
        self.assertEqual(response, TestDataRemoteConnector.TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1)

    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._convert_prompted_host_selection_to_ansible_hosts")
    def test_config_based_host_selection(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()

        def assertion_callback(args):
            self.assertEqual(args[HOST_SELECTION_HOST_ID_1], HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_1])
            self.assertEqual(args[HOST_SELECTION_HOST_ID_2], HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_2])

        RemoteMachineConnector(env.get_collaborators())._run_config_based_host_selection(
            TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS, force_single_conn_info=True
        )
        Assertion.expect_call_argument(self, run_call, "force_single_conn_info", True)
        Assertion.expect_call_argument(self, run_call, "options_list", HOST_SELECTION_OPTIONS_LIST)
        Assertion.expect_call_arguments(self, run_call, "option_to_value_dict", assertion_callback)

    @mock.patch(f"{REMOTE_MACHINE_CONNECTOR_PATH}._convert_prompted_host_selection_to_ansible_hosts")
    def test_run_lan_scan_host_selection(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()

        env.get_collaborators().checks().mock_utility("nmap")
        env.get_collaborators().network_util().mock_lan_network_devices_response(
            ip_range=ARG_IP_DISCOVERY_RANGE,
            response=HOST_SELECTION_OPTIONS_DICT,
        )

        def assertion_callback(args):
            print(args)
            print(args)
            print(args)
            self.assertEqual(args[HOST_SELECTION_HOST_ID_1], HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_1])
            self.assertEqual(args[HOST_SELECTION_HOST_ID_2], HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_2])

        RemoteMachineConnector(env.get_collaborators())._run_lan_scan_host_selection(
            ip_discovery_range=ARG_IP_DISCOVERY_RANGE, force_single_conn_info=True
        )
        Assertion.expect_call_argument(self, run_call, "force_single_conn_info", True)
        Assertion.expect_call_argument(self, run_call, "options_list", HOST_SELECTION_OPTIONS_LIST)
        Assertion.expect_call_arguments(self, run_call, "option_to_value_dict", assertion_callback)

    def test_run_lan_scan_host_selection_fail_missing_nmap(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().checks().mock_utility("nmap", exist=False)
        response = RemoteMachineConnector(env.get_collaborators())._run_lan_scan_host_selection(
            ip_discovery_range=ARG_IP_DISCOVERY_RANGE, force_single_conn_info=True
        )
        self.assertIsNone(response)

    def test_convert_prompted_single_host_selection_to_ansible_hosts(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_single_selection_response(
            "Please choose a network device", HOST_SELECTION_HOST_ID_1
        )
        response = RemoteMachineConnector(env.get_collaborators())._convert_prompted_host_selection_to_ansible_hosts(
            options_list=HOST_SELECTION_OPTIONS_LIST,
            option_to_value_dict=HOST_SELECTION_OPTIONS_DICT,
            force_single_conn_info=True,
        )
        Assertion.expect_equal_objects(
            self, response[0], AnsibleHost.from_dict(HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_1])
        )

    def test_convert_prompted_multiple_host_selection_to_ansible_hosts(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_user_multi_selection_response(
            "Please choose network devices", HOST_SELECTION_OPTIONS_LIST
        )
        response = RemoteMachineConnector(env.get_collaborators())._convert_prompted_host_selection_to_ansible_hosts(
            options_list=HOST_SELECTION_OPTIONS_LIST,
            option_to_value_dict=HOST_SELECTION_OPTIONS_DICT,
            force_single_conn_info=False,
        )
        Assertion.expect_equal_objects(
            self, response[0], AnsibleHost.from_dict(HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_1])
        )
        Assertion.expect_equal_objects(
            self, response[1], AnsibleHost.from_dict(HOST_SELECTION_OPTIONS_DICT[HOST_SELECTION_HOST_ID_2])
        )
