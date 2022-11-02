#!/usr/bin/env python3

import unittest

from common.remote.remote_network_configure import (
    Collaborators,
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureRunner,
)
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    MissingUtilityException,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.test_lib.assertions import Assertion
from external.python_scripts_lib.python_scripts_lib.utils.checks_fakes import FakeChecks
from external.python_scripts_lib.python_scripts_lib.utils.httpclient_fakes import (
    FakeHttpClient,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils_fakes import (
    FakeIOUtils,
)
from external.python_scripts_lib.python_scripts_lib.utils.network_fakes import (
    FakeNetworkUtil,
)
from external.python_scripts_lib.python_scripts_lib.utils.os import (
    LINUX,
    MAC_OS,
    WINDOWS,
    OsArch,
)
from external.python_scripts_lib.python_scripts_lib.utils.printer_fakes import (
    FakePrinter,
)
from external.python_scripts_lib.python_scripts_lib.utils.process_fakes import (
    FakeProcess,
)
from external.python_scripts_lib.python_scripts_lib.utils.prompter_fakes import (
    FakePrompter,
)


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os configure
#
# To run as a single test target:
#  poetry run coverage run -m pytest common/remote/remote_network_configure_test.py
#
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


class RemoteMachineNetworkConfigureTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def create_fake_configure_args(self) -> RemoteMachineNetworkConfigureArgs:
        return RemoteMachineNetworkConfigureArgs(
            node_username="test-user",
            node_password="test-password",
            ip_discovery_range="1.1.1.1/24",
            gw_ip_address="1.1.1.1",
            dns_ip_address="1.1.1.1",
            static_ip_address="1.1.1.200",
            ansible_playbook_path_configure_network="/test/path/ansible/configure_network.yaml",
            ansible_playbook_path_wait_for_network="/test/path/ansible/wait_for_network.yaml",
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker", exist=False)

        runner = RemoteMachineNetworkConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=MissingUtilityException, methodToRun=lambda: runner.prerequisites(ctx, cols.checks)
        )

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineNetworkConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineNetworkConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        runner = RemoteMachineNetworkConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )
        runner = RemoteMachineNetworkConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))