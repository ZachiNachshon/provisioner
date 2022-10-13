#!/usr/bin/env python3

from loguru import logger
from .remote_connector import RemoteMachineConnector
from external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import ProgressIndicator
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter
from external.python_scripts_lib.python_scripts_lib.utils.hosts_file import HostsFile
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import AnsibleRunner, HostIpPair
from external.python_scripts_lib.python_scripts_lib.colors import color


class RemoteMachineNetworkConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    ansible_playbook_path_configure_network: str
    ansible_playbook_path_wait_for_network: str

    def __init__(
        self,
        node_username: str,
        node_password: str,
        ip_discovery_range: str,
        gw_ip_address: str,
        dns_ip_address: str,
        static_ip_address: str,
        ansible_playbook_path_configure_network: str,
        ansible_playbook_path_wait_for_network: str,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.ansible_playbook_path_configure_network = ansible_playbook_path_configure_network
        self.ansible_playbook_path_wait_for_network = ansible_playbook_path_wait_for_network


class Collaborators:
    io: IOUtils
    checks: Checks
    process: Process
    printer: Printer
    prompter: Prompter
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil
    hosts_file: HostsFile


class RemoteMachineNetworkConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)
        self.hosts_file = HostsFile.create(ctx, self.process)


class RemoteMachineNetworkConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineNetworkConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RemoteMachineNetworkConfigureRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )

        ssh_conn_info = remote_connector.collect_ssh_connection_info(
            ctx, args.ip_discovery_range, args.node_username, args.node_password
        )

        dhcpcd_configure_info = remote_connector.collect_dhcpcd_configuration_info(
            ctx, ssh_conn_info.host_ip_address, args.static_ip_address, args.gw_ip_address, args.dns_ip_address
        )

        ansible_vars = [
            f"host_name={ssh_conn_info.hostname}",
            f"static_ip={dhcpcd_configure_info.static_ip_address}",
            f"gateway_address={dhcpcd_configure_info.gw_ip_address}",
            f"dns_address={dhcpcd_configure_info.dns_ip_address}",
        ]

        collaborators.printer.new_line_fn()

        output = collaborators.printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner.run_fn(
                working_dir=collaborators.io.get_current_directory_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                playbook_path=args.ansible_playbook_path_configure_network,
                ansible_vars=ansible_vars,
                ansible_tags=["configure_rpi_network", "define_static_ip", "reboot"],
                selected_hosts=[HostIpPair(host=ssh_conn_info.hostname, ip_address=ssh_conn_info.host_ip_address)],
            ),
            desc_run="Running Ansible playbook (Configure Network)",
            desc_end="Ansible playbook finished (Configure Network).",
        )

        collaborators.printer.new_line_fn()
        collaborators.printer.print_fn(output)
        collaborators.printer.print_with_rich_table_fn(
            generate_instructions_post_network(
                username=ssh_conn_info.username,
                password="REDACTED",
                hostname=ssh_conn_info.hostname,
                ip_address=ssh_conn_info.host_ip_address,
                static_ip=dhcpcd_configure_info.static_ip_address,
            )
        )

        self._maybe_add_hosts_file_entry(
            collaborators.prompter,
            collaborators.hosts_file,
            ssh_conn_info.hostname,
            dhcpcd_configure_info.static_ip_address,
        )

    def _maybe_add_hosts_file_entry(self, prompter: Prompter, hosts_file: HostsFile, hostname: str, static_ip: str):
        if prompter.prompt_yes_no_fn(
            message=f"Add entry '{hostname} {static_ip}' to /etc/hosts file ({color.RED}password required{color.NONE})",
            post_no_message="Skipped adding new entry to /etc/hosts",
            post_yes_message=f"Selected to update /etc/hosts file",
        ):
            hosts_file.add_entry_fn(ip_address=static_ip, dns_names=[hostname], comment="Added by provisioner")

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(generate_logo_configure())
        printer.print_with_rich_table_fn(generate_instructions_pre_network())
        prompter.prompt_for_enter()

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
 ██████╗ ███████╗    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
██╔═══██╗██╔════╝    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
██║   ██║███████╗    ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝
██║   ██║╚════██║    ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗
╚██████╔╝███████║    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
 ╚═════╝ ╚══════╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"""


def generate_instructions_pre_network() -> str:
    return f"""
  This script sets a static IP address on an [yellow]ethernet connected[/yellow] remote Raspberry Pi node.
  It uses DHCPCD (Dynamic Host Configuration Protocol Client Daemon a.k.a DHCP client daemon).

  It is vital for a RPi server to have a predictable address to interact with.
  Every time the Raspberry Pi node will connects to the network, it will use the same address.
"""


def generate_instructions_post_network(ip_address: str, static_ip: str, username: str, password: str, hostname: str):
    return f"""
  [green]Congratulations ![/green]

  You have successfully set a static IP for a Raspberry Pi node:
    • [yellow]{ip_address}[/yellow] --> [yellow]{static_ip}[/yellow]

  To update the node password:
    • SSH into the node - [yellow]ssh {username}@{static_ip}[/yellow] or [yellow]ssh {username}@{hostname}[/yellow] (default pass: {password})
    • Update password   - [yellow]sudo /usr/bin/raspi-config nonint do_change_pass[/yellow]

  To declare the new static node in the provisioner config, add to <ROOT>/config.properties:

    Master:
      • // TODO

    Worker (replace X with the node number):
      • // TODO
"""
