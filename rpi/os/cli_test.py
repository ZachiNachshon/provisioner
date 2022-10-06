#!/usr/bin/env python3

import unittest
from unittest import mock
from typer.testing import CliRunner
from rpi.main import app
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import CliApplicationException

runner = CliRunner()

#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run os install
#
class OsCliTestShould(unittest.TestCase):
    @mock.patch("rpi.os.install.RPiOsInstallRunner.run")
    def test_cli_runner_success(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "install",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        machine_info_args = run_call_kwargs["args"]
        collaborators = run_call_kwargs["collaborators"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(machine_info_args)
        self.assertIsNotNone(collaborators)

    @mock.patch("rpi.os.install.RPiOsInstallRunner.run", side_effect=Exception("runner failure"))
    def test_cli_runner_failure(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "install",
            ],
        )

        self.assertEqual(1, run_call.call_count)
        self.assertIn("Failed to burn Raspbian OS", str(result.stdout))
        self.assertIsInstance(result.exception, CliApplicationException)
        self.assertEqual(str(result.exception), "runner failure")

    def test_integration_darwin_cli_runner_success(self) -> None:
        auto_prompt = "AUTO_PROMPT_RESPONSE"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=darwin_amd64",
                "os",
                "install",
            ],
        )
        cmd_output = str(result.stdout)
        self.assertIn("diskutil list", cmd_output)
        self.assertIn(f"diskutil unmountDisk {auto_prompt}", cmd_output)
        self.assertIn(f"unzip -p DRY_RUN_DOWNLOAD_FILE_PATH | sudo dd of={auto_prompt} bs=1m", cmd_output)
        self.assertIn("sync", cmd_output)
        self.assertIn(f"diskutil unmountDisk {auto_prompt}", cmd_output)
        self.assertIn(f"diskutil mountDisk {auto_prompt}", cmd_output)
        self.assertIn("sudo touch /Volumes/boot/ssh", cmd_output)
        self.assertIn(f"diskutil eject {auto_prompt}", cmd_output)

    def test_integration_linux_cli_runner_success(self) -> None:
        auto_prompt = "AUTO_PROMPT_RESPONSE"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=linux_amd64",
                "os",
                "install",
            ],
        )
        cmd_output = str(result.stdout)
        self.assertIn("lsblk -p", cmd_output)
        self.assertIn(
            f"unzip -p DRY_RUN_DOWNLOAD_FILE_PATH | dd of={auto_prompt} bs=4M conv=fsync status=progress", cmd_output
        )
        self.assertIn("sync", cmd_output)
