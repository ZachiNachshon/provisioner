#!/usr/bin/env python3

from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.process import Process


class FakeProcess(Process):

    __registered_run_commands: List[str] = None
    __mocked_run_commands: dict[str, str] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.__registered_run_commands = []
        self.__mocked_run_commands = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeProcess":
        process = FakeProcess(dry_run=dry_run, verbose=verbose)
        process.run_fn = lambda args, working_dir=None, fail_msg=None, fail_on_error=False, allow_single_shell_command_str=False: process._register_run_command(
            args
        )
        process.is_tool_exist_fn = lambda name: name
        return process

    @staticmethod
    def create(ctx: Context) -> "FakeProcess":
        return FakeProcess._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def mock_run_command(self, args: List[str], expected_output: str):
        cmd_str: str = self._prepare_command_str(args)
        self.__mocked_run_commands[cmd_str] = expected_output

    def _register_run_command(self, args: List[str]) -> str:
        cmd_str: str = self._prepare_command_str(args)
        self.__registered_run_commands.append(cmd_str)
        if cmd_str in self.__mocked_run_commands:
            return self.__mocked_run_commands[cmd_str]
        return None

    def assert_run_command(self, args: List[str]) -> None:
        cmd_str: str = self._prepare_command_str(args)
        print(self.__registered_run_commands)
        if cmd_str not in self.__registered_run_commands:
            raise FakeEnvironmentAssertionError(
                "Process expected command args to be used but they were never provided.\n"
                + f"Actual commands :\n{self.__registered_run_commands}\n"
                + f"Expected:\n{args}"
            )

    def assert_run_commands(self, args: List[List[str]]) -> None:
        for arg in args:
            self.assert_run_command(arg)

    def _prepare_command_str(self, args: List[str]) -> str:
        return " ".join(args) if type(args) == list else str(args)
