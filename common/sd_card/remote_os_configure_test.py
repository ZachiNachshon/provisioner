#!/usr/bin/env python3

import unittest
from unittest import mock
from common.sd_card.remote_os_configure import RemoteMachineConfigureArgs, RemoteMachineConfigureRunner, Collaborators

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    MissingUtilityException,
    CliApplicationException,
)
from external.python_scripts_lib.python_scripts_lib.utils.httpclient_fakes import FakeHttpClient
from external.python_scripts_lib.python_scripts_lib.utils.os import WINDOWS, LINUX, MAC_OS, OsArch
from external.python_scripts_lib.python_scripts_lib.utils.io_utils_fakes import FakeIOUtils
from external.python_scripts_lib.python_scripts_lib.utils.checks_fakes import FakeChecks
from external.python_scripts_lib.python_scripts_lib.utils.process_fakes import FakeProcess
from external.python_scripts_lib.python_scripts_lib.utils.prompter_fakes import FakePrompter
from external.python_scripts_lib.python_scripts_lib.utils.printer_fakes import FakePrinter
from external.python_scripts_lib.python_scripts_lib.utils.httpclient import HttpClient
from external.python_scripts_lib.python_scripts_lib.test_lib.assertions import Assertion
from external.python_scripts_lib.python_scripts_lib.utils.network_fakes import FakeNetworkUtil

# from external.python_scripts_lib.python_scripts_lib.runner.ansible import FakeAnsibleRunner


class FakeCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        print("Creating Fake collaborators...")
        self.io = FakeIOUtils.create(ctx)
        self.process = FakeProcess.create(ctx)
        self.checks = FakeChecks.create(ctx)
        self.prompter = FakePrompter.create(ctx)
        self.printer = FakePrinter.create(ctx)
        self.http_client = FakeHttpClient.create(ctx, self.io)
        # self.ansible_runner = FakeAnsibleRunner.create()
        self.network_util = FakeNetworkUtil.create(ctx)


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os connfigure
#
class RemoteMachineConfigureTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def create_fake_configure_args(self) -> RemoteMachineConfigureArgs:
        return RemoteMachineConfigureArgs(
            node_username="test-user",
            node_password="test-password",
            ip_discovery_range="1.1.1.1/24",
            ansible_playbook_file_path="/test/path/ansible/playbook.yaml",
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)

        runner = RemoteMachineConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=MissingUtilityException, methodToRun=lambda: runner.prerequisites(ctx, cols.checks)
        )

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        runner = RemoteMachineConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )
        runner = RemoteMachineConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

    def test_get_host_ip_address_manual(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("Scan LAN network for RPi IP address at range", False)
        cols.prompter.register_user_input_prompt("Enter RPi node IP address", expected_ip_address)

        runner = RemoteMachineConfigureRunner()
        output = runner._get_host_ip_address(collaborators=cols, ip_discovery_range=None)

        self.assertEqual(expected_ip_address, output)

    def test_get_host_ip_address_lan_network_scan(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("Scan LAN network for RPi IP address at range", True)

        with mock.patch.object(
            RemoteMachineConfigureRunner, "_run_ip_address_selection_flow"
        ) as run_ip_address_selection_flow:

            run_ip_address_selection_flow.return_value = expected_ip_address
            runner = RemoteMachineConfigureRunner()
            output = runner._get_host_ip_address(collaborators=cols, ip_discovery_range=None)

            self.assertEqual(1, run_ip_address_selection_flow.call_count)
            self.assertEqual(expected_ip_address, output)

    def test_get_host_ip_address_fail_to_resolve(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        args = self.create_fake_configure_args()

        with mock.patch.object(RemoteMachineConfigureRunner, "prerequisites") as prerequisites, mock.patch.object(
            RemoteMachineConfigureRunner, "_get_host_ip_address"
        ) as get_host_ip_address:

            prerequisites.return_value = True
            get_host_ip_address.return_value = None

            cols = self.create_fake_collaborators(ctx)

            runner = RemoteMachineConfigureRunner()
            runner.run(ctx=ctx, args=args, collaborators=cols)

            self.assertEqual(1, get_host_ip_address.call_count)
            get_host_ip_address.assert_called_once_with(cols, args.ip_discovery_range)

    def test_get_ssh_connection_info(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        expected_username = "test-user"
        expected_password = "test-pass"
        expected_hostname = "test-host"

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        cols.prompter.register_user_input_prompt("Enter RPi node user", expected_username)
        cols.prompter.register_user_input_prompt("Enter RPi node password", expected_password)
        cols.prompter.register_user_input_prompt("Enter RPi node host name", expected_hostname)

        runner = RemoteMachineConfigureRunner()
        ssh_info_tuple = runner._get_ssh_connection_info(
            ctx, cols.printer, cols.prompter, expected_ip_address, args.node_username, args.node_password
        )

        self.assertEqual(expected_username, ssh_info_tuple[0])
        self.assertEqual(expected_password, ssh_info_tuple[1])
        self.assertEqual(expected_hostname, ssh_info_tuple[2])

    def test_failed_to_get_ssh_username(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        cols.prompter.register_user_input_prompt("Enter RPi node user", None)
        runner = RemoteMachineConfigureRunner()
        ssh_info_tuple = runner._get_ssh_connection_info(
            ctx, cols.printer, cols.prompter, expected_ip_address, args.node_username, args.node_password
        )

        self.assertIsNone(ssh_info_tuple)

    def test_failed_to_get_ssh_password(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        expected_username = "test-user"

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        cols.prompter.register_user_input_prompt("Enter RPi node user", expected_username)
        cols.prompter.register_user_input_prompt("Enter RPi node password", None)
        runner = RemoteMachineConfigureRunner()
        ssh_info_tuple = runner._get_ssh_connection_info(
            ctx, cols.printer, cols.prompter, expected_ip_address, args.node_username, args.node_password
        )

        self.assertIsNone(ssh_info_tuple)

    def test_failed_to_get_ssh_hostname(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "1.1.1.1"
        expected_username = "test-user"
        expected_password = "test-pass"

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        cols.prompter.register_user_input_prompt("Enter RPi node user", expected_username)
        cols.prompter.register_user_input_prompt("Enter RPi node password", expected_password)
        cols.prompter.register_user_input_prompt("Enter RPi node host name", None)
        runner = RemoteMachineConfigureRunner()
        ssh_info_tuple = runner._get_ssh_connection_info(
            ctx, cols.printer, cols.prompter, expected_ip_address, args.node_username, args.node_password
        )

        self.assertIsNone(ssh_info_tuple)

    def test_fail_ip_selection_due_to_missing_nmap(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        runner = RemoteMachineConfigureRunner()
        ip_address = runner._run_ip_address_selection_flow(
            ip_discovery_range=args.ip_discovery_range,
            network_util=cols.network_util,
            checks=cols.checks,
            printer=cols.printer,
            prompter=cols.prompter,
        )

        self.assertIsNone(ip_address)

    def test_get_ip_from_selection_flow(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_ip_address = "192.168.1.1"
        expected_scanned_result = {
            "ip_address": expected_ip_address,
            "hostname": "Remote-OS-Configure-Test-01",
            "status": "Up",
        }

        cols = self.create_fake_collaborators(ctx)
        args = self.create_fake_configure_args()

        cols.checks.register_utility("nmap")
        cols.network_util.register_scan_result(args.ip_discovery_range, expected_scanned_result)
        cols.prompter.register_user_selection_prompt("Please choose a network device", expected_scanned_result)

        runner = RemoteMachineConfigureRunner()
        ip_address = runner._run_ip_address_selection_flow(
            ip_discovery_range=args.ip_discovery_range,
            network_util=cols.network_util,
            checks=cols.checks,
            printer=cols.printer,
            prompter=cols.prompter,
        )

        self.assertIsNotNone(ip_address)
        self.assertEqual(ip_address, expected_ip_address)
