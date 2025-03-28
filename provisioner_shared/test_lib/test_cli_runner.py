#!/usr/bin/env python3

import inspect
import os
import traceback
from typing import List

import click
import click.testing
from click.testing import CliRunner

ENV_VAR_INSTALLER_PLUGIN_TEST = "PROVISIONER_INSTALLER_PLUGIN_TEST"


class CliTestRunnerConfig:
    def __init__(self, is_installer_plugin_test: bool = False):
        self.is_installer_plugin_test = is_installer_plugin_test


class TestCliRunner:
    @staticmethod
    def run_throws_not_managed(cmd: click.BaseCommand, args: List[str] = []) -> click.testing.Result:
        return CliRunner().invoke(cmd, args)

    @staticmethod
    def is_installer_plugin_test() -> bool:
        return os.getenv(key=ENV_VAR_INSTALLER_PLUGIN_TEST, default=False)

    @staticmethod
    def run(cmd: click.BaseCommand, args: List[str] = [], test_cfg: CliTestRunnerConfig = CliTestRunnerConfig()) -> str:
        test_env_vars = {}
        if TestCliRunner.is_installer_plugin_test() or test_cfg.is_installer_plugin_test:
            print("Installer plugin testing mode is enabled")
            test_env_vars = {ENV_VAR_INSTALLER_PLUGIN_TEST: "true"}

        result = CliRunner(mix_stderr=True).invoke(cli=cmd, args=args, env=test_env_vars)

        # Check the exit code to see if there was an issue
        if result.exit_code != 0:

            # error_message = f"Command failed with exit code {result.exit_code}, output: {result.output}"

            # Get the detailed stack trace
            stack_trace = traceback.format_exc()

            # Get the current class name and line number where the error occurred
            frame = inspect.currentframe()
            calling_frame = frame.f_back
            line_number = calling_frame.f_lineno
            class_name = calling_frame.f_globals["__name__"]

            # Include class name and line number in the error details
            error_details = f"\nError occurred in class '{class_name}' at line {line_number}:\n{stack_trace}"

            # Enhanced error output with detailed information
            assert (
                result.exit_code == 0
            ), f"=== TestCliRunner managed assertion error ===\n\nCommand failed with exit code {result.exit_code}\n\n=== OUTPUT ===\n\n{result.output}\n\n=== DETAILS ===\n\n{error_details}"
            # raise AssertionError(f"{error_message}{error_details}")

        else:
            print(f"CLI command ran with no errors:\n{result.output}")

        return result.output
