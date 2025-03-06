#!/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  poetry run coverage run -m pytest -s provisioner/src/main_test.py
#
class TestCLI(unittest.TestCase):

    def test_main_menu_has_expected_base_commands_and_modifiers(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("config        Configuration management", result)
        self.assertIn("plugins       Plugins management", result)
        self.assertIn("version       Print runtime version", result)
        self.assertIn(
            """MODIFIERS
  --verbose, -v          Run command with DEBUG verbosity
  --auto-prompt, -y      Do not prompt for approval and accept everything
  --dry-run, -d          Run command as NO-OP, print commands to output, do not
  execute
  --non-interactive, -n  Turn off interactive prompts and outputs, basic output
  only
  --os-arch TEXT         Specify a OS_ARCH tuple manually
  --help, -h             Show this message and exit.""",
            result,
        )
