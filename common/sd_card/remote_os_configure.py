#!/usr/bin/env python3

from ipaddress import ip_address
import os
from loguru import logger
from external.python_scripts_lib.python_scripts_lib.utils.httpclient import HttpClient
from external.python_scripts_lib.python_scripts_lib.utils.patterns import Patterns
from external.python_scripts_lib.python_scripts_lib.utils.properties import Properties
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.prompter import PromptLevel, Prompter
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import AnsibleRunner, HostIpPair
from external.python_scripts_lib.python_scripts_lib.colors import color

class RemoteMachineConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    ansible_playbook_folder_path: str

    def __init__(self, 
        node_username: str, 
        node_password: str, 
        ip_discovery_range: str, 
        ansible_playbook_folder_path: str) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.ansible_playbook_folder_path = ansible_playbook_folder_path


class Collaborators:
    io = IOUtils
    checks: Checks
    process = Process
    printer = Printer
    prompter = Prompter
    ansible_runner = AnsibleRunner


class RemoteMachineConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx)
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)


class RemoteMachineConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RemoteMachineConfigure run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)

        collaborators.printer.print_fn(template_logo_configure())
        collaborators.printer.print_fn(print_instructions_pre_configure())
        collaborators.prompter.prompt_for_enter()
        collaborators.printer.new_line_fn()

        host_ip_address=""
        if collaborators.prompter.prompt_yes_no_fn("Scan LAN network for RPi IP address"):
          print_instructions_network_scan()
          # NetworkUtils.scan()
        else:
          host_ip_address = collaborators.prompter.prompt_user_input_fn("Enter RPi node IP address")

        if Evaluator.eval_step_failure(ctx, host_ip_address, "Failed to read host IP address"):
            return

        collaborators.printer.print_fn(
          print_instructions_connect_via_ssh(
            ip_address=host_ip_address, 
            user=args.node_username, 
            password="REDACTED"))

        username = collaborators.prompter.prompt_user_input_fn(message="Enter RPi node user", default=args.node_username)
        if Evaluator.eval_step_failure(ctx, username, "Failed to read username"):
            return

        password = collaborators.prompter.prompt_user_input_fn(message="Enter RPi node password", default=args.node_password, redact_default=True)
        if Evaluator.eval_step_failure(ctx, password, "Failed to read password"):
            return

        hostname = collaborators.prompter.prompt_user_input_fn(message="Enter RPi node host name")
        if Evaluator.eval_step_failure(ctx, hostname, "Failed to read hostname"):
            return

        ansible_vars = [f"host_name={hostname}"]

        collaborators.ansible_runner.run_fn(
          username=username,
          password=password,
          playbook_path=args.ansible_playbook_folder_path,
          ansible_vars=ansible_vars,
          selected_hosts=[HostIpPair(host=hostname, ip_address=host_ip_address)]
        )

        collaborators.printer.print_fn(
          print_instructions_post_configure(
            hostname=hostname, 
            ip_address=host_ip_address))


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
  {color.WARNING}Elevated user permissions are required for this step !${color.NONE}

  This step scans all devices on the LAN network and lists the following:
    • IP Address
    • MAC Address
    • Device Name
  ================================================================================================
"""

def print_instructions_connect_via_ssh(ip_address: str, user: str, password: str):
  return f"""
  ================================================================================================
  About to run a script over SSH on address {ip_address}.

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