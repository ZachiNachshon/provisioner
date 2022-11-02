#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

from loguru import logger

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    AnsibleRunner,
    HostIpPair,
)
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import (
    ProgressIndicator,
)
from common.remote.remote_connector import RemoteCliArgs
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter

from ..remote.remote_connector import RemoteMachineConnector

AnchorRunAnsiblePlaybookPath = "common/anchor/playbooks/anchor_run.yaml"

class RunEnvironment(str, Enum):
    Local = "Local"
    Remote = "Remote"

class AnchorRunnerCmdArgs:

    anchor_run_command: str
    github_organization: str
    repository_name: str
    branch_name: str
    github_access_token: str
    remote_args: RemoteCliArgs

    def __init__(
        self,
        anchor_run_command: str,
        github_organization: str,
        repository_name: str,
        branch_name: str,
        github_access_token: str,
        remote_args: Optional[RemoteCliArgs] = None
    ) -> None:
        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.github_access_token = github_access_token
        self.remote_args = remote_args


class Collaborators:
    io: IOUtils
    checks: Checks
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class AnchorCmdRunnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)


class AnchorCmdRunner:
    def run(
        self, 
        ctx: Context, 
        args: AnchorRunnerCmdArgs, 
        collaborators: Collaborators, 
        run_env: RunEnvironment) -> None:

        logger.debug("Inside AnchorCmdRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)

        if run_env == RunEnvironment.Local:
            self._start_local_run_command_flow(ctx, args, collaborators)
        elif run_env == RunEnvironment.Remote:
            self._start_remote_run_command_flow(ctx, args, collaborators)
        else:
            return

    def _start_remote_run_command_flow(
        self, 
        ctx: Context, 
        args: AnchorRunnerCmdArgs, 
        collaborators: Collaborators):

        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )

        ssh_conn_info = remote_connector.collect_ssh_connection_info(ctx, args.remote_args)

        ansible_vars = [
            "anchor_command=Run",
            f"\"anchor_args='{args.anchor_run_command}'\"",
            f"anchor_github_organization={args.github_organization}",
            f"anchor_github_repository={args.repository_name}",
            f"anchor_github_repo_branch={args.branch_name}",
            f"github_access_token={args.github_access_token}",
        ]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=AnchorRunAnsiblePlaybookPath,
                ansible_vars=ansible_vars,
                ansible_tags=["ansible_run"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Anchor Run)",
            desc_end="Ansible playbook finished (Anchor Run).",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)
        collaborators.printer.print_with_rich_table_fn(
            generate_summary(
                host_ip_pairs=ssh_conn_info.host_ip_pairs,
                anchor_cmd={args.anchor_run_command},
            )
        )

    def _start_local_run_command_flow(
        self, 
        ctx: Context, 
        args: AnchorRunnerCmdArgs, 
        collaborators: Collaborators):

        collaborators.process.run_fn(f"anchor {args.anchor_run_command}", allow_single_shell_command_str=True)

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_summary(host_ip_pairs: List[HostIpPair], anchor_cmd: str):
    return f"""
  You have successfully ran an Anchor command on the following remote machines:
  
    • Host Names.....: [yellow]{[pair.host for pair in host_ip_pairs]}[/yellow]
    • IP Addresses...: [yellow]{[pair.ip_address for pair in host_ip_pairs]}[/yellow]
    • Command........: [yellow]anchor {anchor_cmd}[/yellow]
"""
