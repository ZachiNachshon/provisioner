#!/usr/bin/env python3

import unittest
from unittest import mock

from common.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    StepEvaluationFailure,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.test_lib.assertions import Assertion
from external.python_scripts_lib.python_scripts_lib.utils.checks_fakes import FakeChecks
from external.python_scripts_lib.python_scripts_lib.utils.network_fakes import (
    FakeNetworkUtil,
)
from external.python_scripts_lib.python_scripts_lib.utils.os import (
    LINUX,
    MAC_OS,
    OsArch,
)
from external.python_scripts_lib.python_scripts_lib.utils.printer_fakes import (
    FakePrinter,
)
from external.python_scripts_lib.python_scripts_lib.utils.prompter_fakes import (
    FakePrompter,
)


# To run as a single test target:
#  poetry run coverage run -m pytest common/remote/remote_connector_test.py
#
class RemoteMachineConnectorTestShould(unittest.TestCase):
    def create_fake_remote_machine_connector(self, ctx: Context) -> RemoteMachineConnector:
        return RemoteMachineConnector(
            checks=FakeChecks.create(ctx),
            printer=FakePrinter.create(ctx),
            prompter=FakePrompter.create(ctx),
            network_util=FakeNetworkUtil.create(ctx),
        )

    def test_get_host_ip_address_manual(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.prompter.register_yes_no_prompt("Scan LAN network for IP addresses at range", False)
        connector.prompter.register_user_input_prompt("Enter remote node IP address", expected_ip_address)

        output = connector._select_host_ip_pairs(ip_discovery_range=None)

        self.assertEqual(expected_ip_address, output)

    def test_get_host_ip_address_lan_network_scan(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.prompter.register_yes_no_prompt("Scan LAN network for IP addresses at range", True)

        with mock.patch.object(
            RemoteMachineConnector, "_run_ip_address_selection_flow"
        ) as run_ip_address_selection_flow:

            run_ip_address_selection_flow.return_value = expected_ip_address
            output = connector._select_host_ip_pairs(ip_discovery_range=None)

            self.assertEqual(1, run_ip_address_selection_flow.call_count)
            self.assertEqual(expected_ip_address, output)

    def test_get_host_ip_address_fail_to_resolve(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        expected_ip_discovery_range = "1.1.1.1/24"
        expected_node_username = "test-user"
        expected_node_password = "test-pass"
        expected_host_ip_address = "1.1.1.200"

        with mock.patch.object(
            RemoteMachineConnector, "_get_host_ip_address"
        ) as get_host_ip_address, mock.patch.object(
            RemoteMachineConnector, "_get_ssh_connection_info"
        ) as get_ssh_connection_info:

            get_host_ip_address.return_value = expected_host_ip_address

            connector = self.create_fake_remote_machine_connector(ctx)
            connector.collect_ssh_connection_info(
                ctx, expected_ip_discovery_range, expected_node_username, expected_node_password
            )

            self.assertEqual(1, get_host_ip_address.call_count)
            get_host_ip_address.assert_called_once_with(expected_ip_discovery_range)

            self.assertEqual(1, get_ssh_connection_info.call_count)
            get_ssh_connection_info.assert_called_once_with(
                ctx, expected_host_ip_address, expected_node_username, expected_node_password
            )

    def test_get_ssh_connection_info(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        expected_username = "test-user"
        expected_password = "test-pass"
        expected_hostname = "test-host"

        connector = self.create_fake_remote_machine_connector(ctx)

        connector.prompter.register_user_input_prompt("Enter remote node user", expected_username)
        connector.prompter.register_user_input_prompt("Enter remote node password", expected_password)
        connector.prompter.register_user_input_prompt("Enter remote node host name", expected_hostname)

        ssh_info_tuple: SSHConnectionInfo = connector._get_ssh_connection_info(
            ctx, expected_ip_address, expected_username, expected_password
        )

        self.assertEqual(expected_username, ssh_info_tuple.username)
        self.assertEqual(expected_password, ssh_info_tuple.password)
        self.assertEqual(expected_hostname, ssh_info_tuple.hostname)

    def test_failed_to_get_ssh_username(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        arg_username = "default-user"
        arg_password = "default-pass"
        connector = self.create_fake_remote_machine_connector(ctx)

        connector.prompter.register_user_input_prompt("Enter remote node user", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector._get_ssh_connection_info(
                ctx, expected_ip_address, arg_username, arg_password
            ),
        )

    def test_failed_to_get_ssh_password(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        arg_username = "default-user"
        arg_password = "default-pass"
        connector = self.create_fake_remote_machine_connector(ctx)

        connector.prompter.register_user_input_prompt("Enter remote node user", arg_username)
        connector.prompter.register_user_input_prompt("Enter remote node password", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector._get_ssh_connection_info(
                ctx, expected_ip_address, arg_username, arg_password
            ),
        )

    def test_failed_to_get_ssh_hostname(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        arg_username = "default-user"
        arg_password = "default-pass"
        connector = self.create_fake_remote_machine_connector(ctx)

        connector.prompter.register_user_input_prompt("Enter remote node user", arg_username)
        connector.prompter.register_user_input_prompt("Enter remote node password", arg_password)
        connector.prompter.register_user_input_prompt("Enter remote node host name", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector._get_ssh_connection_info(
                ctx, expected_ip_address, arg_username, arg_password
            ),
        )

    def test_fail_ip_selection_due_to_missing_nmap(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.checks.register_utility("nmap", exist=False)
        ip_address = connector._run_lan_scan_selection_flow(ip_discovery_range=None)
        self.assertIsNone(ip_address)

    def test_get_ip_from_selection_flow(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_discovery_range = "192.168.1.1/24"
        expected_ip_address = "192.168.1.200"
        expected_scanned_result = {
            "ip_address": expected_ip_address,
            "hostname": "Remote-OS-Configure-Test-01",
            "status": "Up",
        }

        connector = self.create_fake_remote_machine_connector(ctx)
        connector.checks.register_utility("nmap")
        connector.network_util.register_scan_result(expected_ip_discovery_range, expected_scanned_result)
        connector.prompter.register_user_selection_prompt("Please choose a network device", expected_scanned_result)

        ip_address = connector._run_lan_scan_selection_flow(ip_discovery_range=expected_ip_discovery_range)

        self.assertIsNotNone(ip_address)
        self.assertEqual(ip_address, expected_ip_address)

    def test_collect_dhcpcd_configuration_info(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_host_ip_address = "1.1.1.10"
        expected_static_ip_address = "1.1.1.200"
        expected_gw_ip_address = "1.1.1.1"
        expected_dns_ip_address = "1.1.1.1"

        connector = self.create_fake_remote_machine_connector(ctx)

        connector.prompter.register_user_input_prompt(
            "Enter a desired remote static IP address", expected_static_ip_address
        )
        connector.prompter.register_user_input_prompt("Enter the gateway address", expected_gw_ip_address)
        connector.prompter.register_user_input_prompt("Enter the DNS resolver address", expected_dns_ip_address)

        dhcpd_config_info: DHCPCDConfigurationInfo = connector.collect_dhcpcd_configuration_info(
            ctx, expected_host_ip_address, expected_static_ip_address, expected_gw_ip_address, expected_dns_ip_address
        )

        self.assertEqual(expected_static_ip_address, dhcpd_config_info.static_ip_address)
        self.assertEqual(expected_gw_ip_address, dhcpd_config_info.gw_ip_address)
        self.assertEqual(expected_dns_ip_address, dhcpd_config_info.dns_ip_address)

    def test_failed_to_collect_static_ip_address(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.prompter.register_user_input_prompt("Enter a desired remote static IP address", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector.collect_dhcpcd_configuration_info(ctx, None, None, None, None),
        )

    def test_failed_to_collect_gateway_ip_address(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        expected_static_ip_address = "1.1.1.200"
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.prompter.register_user_input_prompt(
            "Enter a desired remote static IP address", expected_static_ip_address
        )
        connector.prompter.register_user_input_prompt("Enter the gateway address", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector.collect_dhcpcd_configuration_info(ctx, None, None, None, None),
        )

    def test_failed_to_collect_dns_ip_address(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        expected_static_ip_address = "1.1.1.200"
        expected_gw_ip_address = "1.1.1.1"
        connector = self.create_fake_remote_machine_connector(ctx)
        connector.prompter.register_user_input_prompt(
            "Enter a desired remote static IP address", expected_static_ip_address
        )
        connector.prompter.register_user_input_prompt("Enter the gateway address", expected_gw_ip_address)
        connector.prompter.register_user_input_prompt("Enter the DNS resolver address", None)
        Assertion.expect_failure(
            self,
            ex_type=StepEvaluationFailure,
            methodToRun=lambda: connector.collect_dhcpcd_configuration_info(ctx, None, None, None, None),
        )
