#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsibleHost, AnsibleRunnerLocal
from provisioner_shared.components.runtime.runner.ansible.ansible_test import ANSIBLE_DUMMY_PLAYBOOK
from provisioner_shared.components.runtime.utils.io_utils import IOUtils
from provisioner_shared.components.runtime.utils.paths import Paths
from provisioner_shared.test_lib.cli_container import RemoteSSHContainer
from provisioner_shared.test_lib.docker.dockerized import dockerized
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

#
# !! Run within a Docker container !!
#


# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner/src/test_dummy.py --e2e
#
@pytest.mark.e2e
class TestCLI(unittest.TestCase):

    # Run before each test
    # def setUp(self):
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        # cls.container = RemoteSSHContainer(CoreCollaborators(Context.create_empty()), allow_logging=True)
        cls.container = RemoteSSHContainer()
        cls.container.start()

    # Stop after each test
    # def setUp(self):
    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if cls.container:
            cls.container.stop()
            cls.container = None  # Ensure cleanup

    # @unittest.SkipTest
    @dockerized()
    def test_run_inside_docker(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        # self.assertEqual(result.exit_code, 0)
        self.assertIn("USAGE", result)

    @unittest.SkipTest
    def test_run_cli_with_docker_over_ssh(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "examples",
                "ansible",
                "--environment",
                "Remote",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "hello",
                "-vy",
            ],
        )
        print("-------------------------------------")
        print(result)
        print("-------------------------------------")
        self.assertTrue(False)

    @unittest.SkipTest
    def test_run_install_cli_util(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "install",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "cli",
                "anchor",
                "-vy",
            ],
        )
        print("-------------------------------------")
        print(result)
        print("-------------------------------------")
        self.assertTrue(False)

    @unittest.SkipTest
    def test_interact_with_docker_over_ssh(self):
        assert self.container._container, "Container failed to start!"
        print(f"Started container: {self.container._container.short_id}")

        # result = self.container.exec("ls -la")
        # assert result is not None, "Execution failed!"
        # print(f"Command output: {result.output.decode('utf-8')}")

        try:
            print("===============================================")
            print(self.container._container.short_id)  # Should print the container ID
            print("===============================================")
            ctx = Context.create(dry_run=False, verbose=True, auto_prompt=True)
            print("After context creation: ", ctx.__dict__)
            AnsibleRunnerLocal.create(
                ctx=ctx,
                io_utils=IOUtils.create(ctx),
                paths=Paths.create(ctx),
            ).run_fn(
                selected_hosts=[
                    AnsibleHost(host="localhost", ip_address="127.0.0.1:2222", username="pi", password="raspberry")
                ],
                playbook=ANSIBLE_DUMMY_PLAYBOOK,
            ),
            # Run tests
            # self.container
            assert self.container._container  # Ensure it actually exists
            result = self.container.exec("ls -la")
            assert result is not None
            print(result.output.decode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")
            raise e

        # self.assertTrue(False)
