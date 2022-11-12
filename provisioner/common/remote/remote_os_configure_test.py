#!/usr/bin/env python3

import unittest

from provisioner.common.remote.remote_os_configure import (
    Collaborators,
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    MissingUtilityException,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.test_lib.assertions import Assertion
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.checks_fakes import FakeChecks
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.httpclient_fakes import (
    FakeHttpClient,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.io_utils_fakes import (
    FakeIOUtils,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.network_fakes import (
    FakeNetworkUtil,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.os import (
    LINUX,
    MAC_OS,
    WINDOWS,
    OsArch,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.printer_fakes import (
    FakePrinter,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.process_fakes import (
    FakeProcess,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.prompter_fakes import (
    FakePrompter,
)


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os configure
#
# To run as a single test target:
#  poetry run coverage run -m pytest common/remote/remote_os_configure_test.py
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


class RemoteMachineConfigureTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def create_fake_configure_args(self) -> RemoteMachineOsConfigureArgs:
        return RemoteMachineOsConfigureArgs(
            node_username="test-user",
            node_password="test-password",
            ip_discovery_range="1.1.1.1/24",
            ansible_playbook_path_configure_os="/test/path/ansible/playbook.yaml",
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker", exist=False)

        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=MissingUtilityException, methodToRun=lambda: runner.prerequisites(ctx, cols.checks)
        )

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))
