#!/usr/bin/env python3

import inspect
import traceback
from typing import List
import click
from click.testing import CliRunner, Result

class TestCliRunner:
    @staticmethod
    def run(cmd: click.BaseCommand, args: List[str] = []) -> None:
        result = CliRunner().invoke(cmd, args)

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
            assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\noutput: {result.output}\ndetails: {error_details}"
            # raise AssertionError(f"{error_message}{error_details}")

        else:
            print(f"Command succeeded: {result.output}")
