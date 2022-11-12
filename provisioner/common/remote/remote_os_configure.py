#!/usr/bin/env python3

from loguru import logger

from provisioner.common.remote.remote_connector import RemoteCliArgs, RemoteMachineConnector, SSHConnectionInfo
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from provisioner.external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    AnsibleRunner,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.json_util import JsonUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.process import Process
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import (
    ProgressIndicator,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.summary import Summary

class RemoteMachineOsConfigureArgs:

    ansible_playbook_path_configure_os: str
    remote_args: RemoteCliArgs

    def __init__(self, remote_args: RemoteCliArgs, ansible_playbook_path_configure_os: str) -> None:
        self.remote_args = remote_args
        self.ansible_playbook_path_configure_os = ansible_playbook_path_configure_os


class Collaborators:
    io: IOUtils
    checks: Checks
    json_util: JsonUtil
    summary: Summary
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class RemoteMachineOsConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.json_util = JsonUtil.create(ctx, self.io)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)
        self.summary = Summary.create(ctx, self.json_util, self.printer, self.prompter)


class RemoteMachineOsConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineOsConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RemoteMachineOsConfigureRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )

        ssh_conn_info = Evaluator.eval_step_failure_throws(
            call=lambda: remote_connector.collect_ssh_connection_info(
                ctx, args.remote_args, force_single_conn_info=True
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary.add_values("ssh_conn_info", ssh_conn_info)

        hostname_ip_tuple = self._extract_host_ip_tuple(ctx, ssh_conn_info)
        ssh_hostname = hostname_ip_tuple[0]
        ssh_ip_address = hostname_ip_tuple[1]
        ansible_vars = [f"host_name={ssh_hostname}"]

        collaborators.summary.show_summary_and_prompt_for_enter("Configure OS")

        print("=======================================================")
        print(f"PWD: {collaborators.io.get_current_directory_fn()}")
        print("=======================================================")

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
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
            generate_instructions_post_configure(hostname=ssh_hostname, ip_address=ssh_ip_address)
        )

    def _extract_host_ip_tuple(self, ctx: Context, ssh_conn_info: SSHConnectionInfo) -> tuple[str, str]:
        if ctx.is_dry_run():
            return ("DRY_RUN_RESPONSE", "DRY_RUN_RESPONSE")
        else:
            # Promised to have only single item
            single_pair_item = ssh_conn_info.host_ip_pairs[0]
            return (single_pair_item.host, single_pair_item.ip_address)

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
  Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
  Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.

  Complete the following steps:
    1. Eject the SD-Card
    2. Connect the SD-Card to a Raspberry Pi node
    3. Connect the Raspberry Pi node to a power supply
    4. Connect the Raspberry Pi node to the network
"""


def generate_instructions_post_configure(hostname: str, ip_address: str):
    return f"""
  You have successfully configured hardware and system settings for a Raspberry Pi node:
  
    • Host Name....: [yellow]{hostname}[/yellow]
    • IP Address...: [yellow]{ip_address}[/yellow]
"""
