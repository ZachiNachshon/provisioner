#!/usr/bin/env python3

from typing import List, Optional

from ..infra.context import Context
from .process import Process


class FakeProcess(Process):

    registered_commands: dict[str, str] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.registered_commands = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeProcess":
        process = FakeProcess(dry_run=dry_run, verbose=verbose)
        process.run_fn = lambda args, working_dir=None, fail_msg=None, fail_on_error=False, allow_single_shell_command_str=False: process._command_selector(
            args
        )
        process.is_tool_exist_fn = lambda name: name
        return process

    @staticmethod
    def create(ctx: Context) -> "FakeProcess":
        return FakeProcess._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def register_command(self, cmd_str: str, expected_output: str):
        # When opting to use the FakeProcess instead of mocking via @mock.patch, we'll override the run function
        self.registered_commands[cmd_str] = expected_output

    def _command_selector(self, args: List[str]) -> str:
        cmd_str: str = " ".join(args) if type(args) == list else str(args)
        if cmd_str not in self.registered_commands:
            raise LookupError("Fake process command is not defined. name: " + cmd_str)
        return self.registered_commands.get(cmd_str)
