#!/usr/bin/env python3

from typing import List
from loguru import logger
from external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import ProgressIndicator
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import AnsibleRunner, HostIpPair
from external.python_scripts_lib.python_scripts_lib.colors import color


class RemoteMachineConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    ansible_playbook_file_path: str

    def __init__(
        self, node_username: str, node_password: str, ip_discovery_range: str, ansible_playbook_file_path: str
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.ansible_playbook_file_path = ansible_playbook_file_path


class Collaborators:
    io: IOUtils
    checks: Checks
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class RemoteMachineConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)


class RemoteMachineConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RemoteMachineConfigure run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        host_ip_address = self._get_host_ip_address(collaborators, args.ip_discovery_range)
        if Evaluator.eval_step_failure(ctx, host_ip_address, "Failed to read host IP address"):
            return

        # Get a tuple of (username, password, hostname)
        conn_info_tuple = self._get_ssh_connection_info(
            ctx, collaborators.printer, collaborators.prompter, host_ip_address, args.node_username, args.node_password
        )

        username = conn_info_tuple[0]
        password = conn_info_tuple[1]
        hostname = conn_info_tuple[2]

        ansible_vars = [f"host_name={hostname}"]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=username,
                password=password,
                playbook_path=args.ansible_playbook_file_path,
                ansible_vars=ansible_vars,
                selected_hosts=[HostIpPair(host=hostname, ip_address=host_ip_address)],
            ),
            desc_run="Running Ansible playbook",
            desc_end="Ansible playbook finished.",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)
        collaborators.printer.print_fn(print_instructions_post_configure(hostname=hostname, ip_address=host_ip_address))

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(template_logo_configure())
        printer.print_fn(print_instructions_pre_configure())
        prompter.prompt_for_enter()

    def _get_host_ip_address(self, collaborators: Collaborators, ip_discovery_range: str) -> str:
        if collaborators.prompter.prompt_yes_no_fn(
            message=f"Scan LAN network for RPi IP address at range {ip_discovery_range}",
            post_no_message="Skipped LAN network scan",
            post_yes_message=f"Selected to scan LAN at range {ip_discovery_range}",
        ):

            return self._run_ip_address_selection_flow(
                ip_discovery_range,
                collaborators.network_util,
                collaborators.checks,
                collaborators.printer,
                collaborators.prompter,
            )
        else:
            collaborators.printer.new_line_fn()
            return collaborators.prompter.prompt_user_input_fn(
                message="Enter RPi node IP address", post_user_input_message="Selected IP address :: "
            )

    def _get_ssh_connection_info(
        self,
        ctx: Context,
        printer: Printer,
        prompter: Prompter,
        host_ip_address: str,
        arg_username: str,
        arg_password: str,
    ) -> tuple[str, str, str]:

        printer.print_fn(
            print_instructions_connect_via_ssh(ip_address=host_ip_address, user=arg_username, password="REDACTED")
        )

        username = prompter.prompt_user_input_fn(
            message="Enter RPi node user", default=arg_username, post_user_input_message="Selected RPi user     :: "
        )
        if Evaluator.eval_step_failure(ctx, username, "Failed to read username"):
            return

        password = prompter.prompt_user_input_fn(
            message="Enter RPi node password",
            default=arg_password,
            post_user_input_message="Selected RPi password :: ",
            redact_default=True,
        )
        if Evaluator.eval_step_failure(ctx, password, "Failed to read password"):
            return

        hostname = prompter.prompt_user_input_fn(
            message="Enter RPi node host name", post_user_input_message="Selected RPi hostname :: "
        )
        if Evaluator.eval_step_failure(ctx, hostname, "Failed to read hostname"):
            return

        return (username, password, hostname)

    def _run_ip_address_selection_flow(
        self, ip_discovery_range: str, network_util: NetworkUtil, checks: Checks, printer: Printer, prompter: Prompter
    ) -> str:

        if not checks.is_tool_exist_fn("nmap"):
            logger.warning("Missing mandatory utility. name: nmap")
            return None

        printer.print_fn(print_instructions_network_scan())
        scan_dict = network_util.get_all_lan_network_devices_fn(ip_range=ip_discovery_range)
        printer.new_line_fn()

        options_dict: List[dict] = []
        for scan_item in scan_dict:
            options_dict.append(scan_dict[scan_item])

        selected_scanned_item: dict = prompter.prompt_user_selection_fn(
            message="Please choose a network device", options=options_dict
        )

        return selected_scanned_item["ip_address"] if selected_scanned_item is not None else None

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def template_logo_configure() -> str:
    return f"""
 ██████╗ ███████╗     ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗ ██╗   ██╗██████╗ ███████╗
██╔═══██╗██╔════╝    ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝ ██║   ██║██╔══██╗██╔════╝
██║   ██║███████╗    ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗██║   ██║██████╔╝█████╗
██║   ██║╚════██║    ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║██║   ██║██╔══██╗██╔══╝
╚██████╔╝███████║    ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝╚██████╔╝██║  ██║███████╗
 ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝
"""


def print_instructions_pre_configure() -> str:
    return f"""
  ================================================================================================
  This script configures Raspbian OS software and hardware settings on a remote Raspberry Pi node.
  Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.

  Complete the following steps:
    1. Eject the SD-Card
    2. Connect the SD-Card to a Raspberry Pi node
    3. Connect the Raspberry Pi node to a power supply
    4. Connect the Raspberry Pi node to the network
  ================================================================================================
"""


def print_instructions_network_scan() -> str:
    return f"""
  ================================================================================================
  Required mandatory locally installed utility: {color.WARNING}nmap{color.NONE}.
  {color.WARNING}Elevated user permissions are required for this step !{color.NONE}

  This step scans all devices on the LAN network and lists the following:

    • IP Address
    • Device Name
  ================================================================================================
"""


def print_instructions_connect_via_ssh(ip_address: str, user: str, password: str):
    return f"""
  ================================================================================================
  About to run a script over SSH on address {color.WARNING}{ip_address}{color.NONE}.

  Requirements:
    • Ansible or Docker
      If Ansible is missing, a Docker image will be built and used instead.

  {color.WARNING}This step prompts for connection access information (press ENTER for defaults):
    • Raspberry Pi node user     (default: {user})
    • Raspberry Pi node password (default: {password}){color.NONE}

  To change the default values, please refer to the documentation.
  ================================================================================================
"""


def print_instructions_post_configure(hostname: str, ip_address: str):
    return f"""
  ================================================================================================
  You have successfully configured hardware and system settings for a Raspberry Pi node:
  
    • Host Name....: {hostname}
    • IP Address...: {ip_address}
  ================================================================================================
"""
