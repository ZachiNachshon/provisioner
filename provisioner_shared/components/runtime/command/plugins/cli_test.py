#!/usr/bin/env python3

import unittest

from provisioner_shared.components.runtime.test_lib.test_env import TestEnv
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_cli_runner import TestCliRunner

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/command/plugins/cli_test.py
#
class PluginsCliTestShould(unittest.TestCase):
    env = TestEnv.create()

    def test_e2e_cli_plugins_list_cmd_success(self) -> None:
        cli_app = self.env.create_cli_app()
        Assertion.expect_success(
            self, 
            method_to_run=lambda: TestCliRunner.run(
            cli_app,
            [
                "plugins",
                "install",
                "--name",
                "provisioner_examples_plugin",
            ],
        ))

        Assertion.expect_output(
            self,
            expected="""Name........: Examples
Desc........: Playground for using the CLI framework with basic dummy commands
Maintainer..: Zachi Nachshon""",
            method_to_run=lambda: TestCliRunner.run(
            cli_app,
            [
                "plugins",
                "list",
            ],
        ))

        Assertion.expect_success(
            self, 
            method_to_run=lambda: TestCliRunner.run(
            cli_app,
            [
                "plugins",
                "uninstall",
                "--name",
                "provisioner_examples_plugin",
            ],
        ))
