#!/usr/bin/env python3

from typing import List

from ...infra.context import Context
from ...utils.io_utils import IOUtils
from ...utils.process import Process
from .ansible import AnsibleRunner


class FakeAnsibleRunner(AnsibleRunner):

    registered_commands: dict[str, str] = {}

    def __init__(
        self, io_utils: IOUtils, process: Process, dry_run: bool, verbose: bool, ansible_shell_runner_path: str
    ) -> None:

        super().__init__(
            io_utils=io_utils,
            process=process,
            dry_run=dry_run,
            verbose=verbose,
            ansible_shell_runner_path=ansible_shell_runner_path,
        )
        self.registered_commands = {}

    @staticmethod
    def _create_fake(io_utils: IOUtils, process: Process, dry_run: bool, verbose: bool) -> "FakeAnsibleRunner":

        ansible_runner = FakeAnsibleRunner(io_utils=io_utils, process=process, dry_run=dry_run, verbose=verbose)
        ansible_runner.run_fn = lambda username, password, working_dir, selected_hosts, playbook_path, ansible_vars=None, force_dockerized=False: ansible_runner._command_selector(
            username, password, working_dir, selected_hosts, playbook_path, ansible_vars, force_dockerized=False
        )
        return ansible_runner

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils, process: Process) -> "FakeAnsibleRunner":
        return FakeAnsibleRunner._create_fake(
            io_utils=io_utils,
            process=process,
            dry_run=ctx.is_dry_run(),
            verbose=ctx.is_verbose(),
            ansible_shell_runner_path="/path/to/ansible/shell/runner/ansible.sh",
        )

    def register_command(self, cmd_str: str, expected_output: str):
        # When opting to use the FakeProcess instead of mocking via @mock.patch, we'll override the run function
        self.registered_commands[cmd_str] = expected_output

    def _command_selector(self, args: List[str]) -> str:
        cmd_str: str = " ".join(args) if type(args) == list else str(args)
        if cmd_str not in self.registered_commands:
            raise LookupError("Fake process command is not defined. name: " + cmd_str)
        return self.registered_commands.get(cmd_str)
