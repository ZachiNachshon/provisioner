#!/usr/bin/env python3

from typing import List
from loguru import logger

from external.python_scripts_lib.python_scripts_lib.colors import color
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

from .remote_connector import RemoteMachineConnector


class RemoteK3sManagerArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    ansible_playbook_path_configure_os: str

    def __init__(
        self, node_username: str, node_password: str, ip_discovery_range: str, ansible_playbook_path_configure_os: str
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.ansible_playbook_path_configure_os = ansible_playbook_path_configure_os


class Collaborators:
    io: IOUtils
    checks: Checks
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class RemoteK3sManagerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)


class RemoteK3sManagerRunner:
    def run(self, ctx: Context, args: RemoteK3sManagerArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RemoteK3sManagerRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )

        ssh_conn_info = remote_connector.collect_ssh_connection_info(
            ctx, args.ip_discovery_range, args.node_username, args.node_password
        )

        # TODO: need adjustments
        ansible_vars = [f"host_name={pair.host}" for pair in ssh_conn_info.host_ip_pairs]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                playbook_path=args.ansible_playbook_path_configure_os,
                ansible_vars=ansible_vars,
                ansible_tags=["configure_remote_node", "reboot"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Configure OS)",
            desc_end="Ansible playbook finished (Configure OS).",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)
        collaborators.printer.print_with_rich_table_fn(
            generate_instructions_post_configure(
                host_ip_pairs=ssh_conn_info.host_ip_address
            )
        )

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(generate_logo_configure())
        printer.print_with_rich_table_fn(generate_instructions_pre_configure())
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


def generate_logo_configure() -> str:
    return f"""
 ██████╗ ███████╗     ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗ ██╗   ██╗██████╗ ███████╗
██╔═══██╗██╔════╝    ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝ ██║   ██║██╔══██╗██╔════╝
██║   ██║███████╗    ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗██║   ██║██████╔╝█████╗
██║   ██║╚════██║    ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║██║   ██║██╔══██╗██╔══╝
╚██████╔╝███████║    ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝╚██████╔╝██║  ██║███████╗
 ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝
"""


def generate_instructions_pre_configure() -> str:
    return f"""
  This script configures Raspbian OS software and hardware settings on a remote Raspberry Pi node.
  Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.

  Complete the following steps:
    1. Eject the SD-Card
    2. Connect the SD-Card to a Raspberry Pi node
    3. Connect the Raspberry Pi node to a power supply
    4. Connect the Raspberry Pi node to the network
"""


def generate_instructions_post_configure(host_ip_pairs: List[HostIpPair]):
    return f"""
  You have successfully configured hardware and system settings for a Raspberry Pi node:
  
    • Host Name....: [yellow]{[pair.host for pair in host_ip_pairs]}[/yellow]
    • IP Address...: [yellow]{[pair.ip_address for pair in host_ip_pairs]}[/yellow]
"""
