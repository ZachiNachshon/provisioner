#!/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  ./run_tests.py provisioner/src/main_test.py
#
class TestCLI(unittest.TestCase):

    def test_main_menu_has_expected_base_commands_and_modifiers(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("config", result)
        self.assertIn("Configuration management", result)
        self.assertIn("plugins", result)
        self.assertIn("Plugins management", result)
        self.assertIn("version", result)
        self.assertIn("Print runtime version", result)
        self.assertIn("MODIFIERS", result)
        self.assertIn("--verbose, -v", result)
        self.assertIn("Run command with DEBUG verbosity", result)
        self.assertIn("--auto-prompt, -y", result)
        self.assertIn("Do not prompt for approval and accept everything", result)
        self.assertIn("--dry-run, -d", result)
        self.assertIn("Run command as NO-OP, print commands to output", result)
        self.assertIn("--non-interactive, -n", result)
        self.assertIn("Turn off interactive prompts and outputs", result)
        self.assertIn("--os-arch TEXT", result)
        self.assertIn("Specify a OS_ARCH tuple manually", result)
        self.assertIn("--package-manager [pip|uv]", result)
        self.assertIn("Specify a Python package manager  [default: pip]", result)
        self.assertIn("--help, -h", result)
        self.assertIn("Show this message and exit.", result)
