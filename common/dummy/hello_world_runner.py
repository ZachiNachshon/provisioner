#!/usr/bin/env python3

from loguru import logger

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    AnsibleRunner,
    HostIpPair,
)
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import (
    ProgressIndicator,
)
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter

from ..remote.remote_connector import RemoteCliArgs, SSHConnectionInfo

HelloWorldAnsiblePlaybookPath = "example/dummy/playbooks/hello_world.yaml"

class HelloWorldRunnerArgs:

    username: str
    remote_args: RemoteCliArgs

    def __init__(
        self,
        username: str,
        remote_args: RemoteCliArgs
    ) -> None:

        self.username = username
        self.remote_args = remote_args


class RunnerCollaborators:
    io: IOUtils
    checks: Checks
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner


class HelloWorldRunnerCollaborators(RunnerCollaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)


class HelloWorldRunner:
    def run(self, ctx: Context, args: HelloWorldRunnerArgs, collaborators: RunnerCollaborators) -> None:
        logger.debug("Inside HelloWorldRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        ssh_conn_info = SSHConnectionInfo(
            username="pi", password="raspbian", host_ip_pairs=[HostIpPair(host="localhost", ip_address="ansible_connection=local")]
        )

        ansible_vars = [f"\"username='{args.username}'\""]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=HelloWorldAnsiblePlaybookPath,
                ansible_vars=ansible_vars,
                ansible_tags=["hello"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Hello World)",
            desc_end="Ansible playbook finished (Hello World).",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        prompter.prompt_for_enter_fn()

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")
