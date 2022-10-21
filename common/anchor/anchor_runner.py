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
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter

from ..remote.remote_connector import RemoteMachineConnector

RunEnvironment = Enum("RunEnvironmen", "Local Remote")
AnchorRunAnsiblePlaybookPath = "common/anchor/playbooks/anchor_run.yaml"


class AnchorRunnerCmdArgs:

    anchor_run_command: str
    github_organization: str
    repository_name: str
    branch_name: str
    git_access_token: str

    # Optional arguments only for remote anchor run
    node_username: str
    node_password: str
    ip_discovery_range: str

    def __init__(
        self,
        anchor_run_command: str,
        github_organization: str,
        repository_name: str,
        branch_name: str,
        git_access_token: str,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
    ) -> None:

        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.git_access_token = git_access_token
        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range


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
    def run(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside AnchorRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)

        # TODO: print a list of available installers

        run_env = self._ask_for_run_environment(collaborators.prompter)
        if run_env == RunEnvironment.Local:
            self._start_local_run_command_flow(ctx, args, collaborators)
        elif run_env == RunEnvironment.Remote:
            self._start_remote_run_command_flow(ctx, args, collaborators)
        else:
            return

    def _ask_for_run_environment(self, prompter: Prompter) -> RunEnvironment:
        options_dict: List[dict] = ["Local", "Remote"]
        selected_scanned_item: dict = prompter.prompt_user_selection_fn(
            message="Please choose an environment to run anchor command on", options=options_dict
        )
        if selected_scanned_item == "Local":
            return RunEnvironment.Local
        elif selected_scanned_item == "Remote":
            return RunEnvironment.Remote
        return None

    def _start_remote_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: Collaborators):
        collaborators.printer.print_with_rich_table_fn(notify_before_remote_execution())
        collaborators.prompter.prompt_for_enter()

        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )

        ssh_conn_info = remote_connector.collect_ssh_connection_info(
            ctx, args.ip_discovery_range, args.node_username, args.node_password
        )

        ansible_vars = [
            "anchor_command=Run",
            f"\"anchor_args='{args.anchor_run_command}'\"",
            f"anchor_github_organization={args.github_organization}",
            f"anchor_github_repository={args.repository_name}",
            f"anchor_github_repo_branch={args.branch_name}",
            f"git_access_token={args.git_access_token}",
        ]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                playbook_path=AnchorRunAnsiblePlaybookPath,
                ansible_vars=ansible_vars,
                ansible_tags=["ansible_run"],
                selected_hosts=[HostIpPair(host=ssh_conn_info.hostname, ip_address=ssh_conn_info.host_ip_address)],
            ),
            desc_run="Running Ansible playbook (Anchor Run)",
            desc_end="Ansible playbook finished (Anchor Run).",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)
        collaborators.printer.print_with_rich_table_fn(
            generate_summary(
                hostname=ssh_conn_info.hostname,
                ip_address=ssh_conn_info.host_ip_address,
                anchor_cmd={args.anchor_run_command},
            )
        )

    def _start_local_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: Collaborators):
        collaborators.printer.print_with_rich_table_fn(notify_before_local_execution())
        collaborators.prompter.prompt_for_enter()

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def notify_before_remote_execution() -> str:
    return f"""
  About to run an anchor command on remote machine.
"""


def notify_before_local_execution() -> str:
    return f"""
  About to run an anchor command locally.
"""


def generate_summary(hostname: str, ip_address: str, anchor_cmd: str):
    return f"""
  You have successfully ran an Anchor command on the remote machine:
  
    • Host Name....: [yellow]{hostname}[/yellow]
    • IP Address...: [yellow]{ip_address}[/yellow]
    • Command......: [yellow]anchor {anchor_cmd}[/yellow]
"""
