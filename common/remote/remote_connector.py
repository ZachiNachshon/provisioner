#!/usr/bin/env python3

from typing import List, Optional
from loguru import logger
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter


class SSHConnectionInfo:
    username: str
    password: str
    hostname: str
    host_ip_address: str

    def __init__(self, username: str, password: str, hostname: str, host_ip_address: str) -> None:
        self.username = username
        self.password = password
        self.hostname = hostname
        self.host_ip_address = host_ip_address


class DHCPCDConfigurationInfo:
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str

    def __init__(self, gw_ip_address: str, dns_ip_address: str, static_ip_address: str) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address


class RemoteMachineConnector:

    checks: Checks = None
    network_util: NetworkUtil = None
    printer: Printer = None
    prompter: Prompter = None

    def __init__(self, checks: Checks, printer: Printer, prompter: Prompter, network_util: NetworkUtil) -> None:
        self.checks = checks
        self.network_util = network_util
        self.printer = printer
        self.prompter = prompter

    def collect_ssh_connection_info(
        self,
        ctx: Context,
        ip_discovery_range: str,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
    ) -> SSHConnectionInfo:

        """
        Prompt the user for required remote SSH connection parameters
        """
        host_ip_address = Evaluator.eval_step_failure_throws(
            call=lambda: self._get_host_ip_address(ip_discovery_range),
            ctx=ctx,
            err_msg="Failed to read host IP address",
        )

        return self._get_ssh_connection_info(ctx, host_ip_address, node_username, node_password)

    def collect_dhcpcd_configuration_info(
        self, ctx: Context, host_ip_address: str, arg_static_ip: str, arg_gw_address: str, arg_dns_address: str
    ) -> DHCPCDConfigurationInfo:

        self.printer.print_with_rich_table_fn(
            generate_instructions_dhcpcd_config(
                ip_address=host_ip_address, default_gw_address=arg_gw_address, default_dns_address=arg_dns_address
            )
        )

        selected_static_ip = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter a desired remote static IP address (example: 192.168.1.2XX)",
                default=arg_static_ip,
                post_user_input_message="Selected remote static IP address       :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read static IP address",
        )

        selected_gw_address = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter the gateway address",
                default=arg_gw_address,
                post_user_input_message="Selected gateway address                :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read gateway IP address",
        )

        selected_dns_resolver_address = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter the DNS resolver address",
                default=arg_dns_address,
                post_user_input_message="Selected remote DNS resolver IP address :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read DNS resolver IP address",
        )

        return DHCPCDConfigurationInfo(selected_gw_address, selected_dns_resolver_address, selected_static_ip)

    def _get_host_ip_address(self, ip_discovery_range: str) -> str:
        if self.prompter.prompt_yes_no_fn(
            message=f"Scan LAN network for IP addresses at range {ip_discovery_range}",
            post_no_message="Skipped LAN network scan",
            post_yes_message=f"Selected to scan LAN at range {ip_discovery_range}",
        ):
            return self._run_ip_address_selection_flow(ip_discovery_range)
        else:
            self.printer.new_line_fn()
            return self.prompter.prompt_user_input_fn(
                message="Enter remote node IP address", post_user_input_message="Selected IP address :: "
            )

    def _get_ssh_connection_info(
        self,
        ctx: Context,
        host_ip_address: str,
        arg_username: str,
        arg_password: str,
    ) -> SSHConnectionInfo:

        self.printer.print_with_rich_table_fn(
            generate_instructions_connect_via_ssh(ip_address=host_ip_address, user=arg_username, password="REDACTED")
        )

        username = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter remote node user",
                default=arg_username,
                post_user_input_message="Selected remote user     :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read username",
        )

        password = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter remote node password",
                default=arg_password,
                post_user_input_message="Selected remote password :: ",
                redact_default=True,
            ),
            ctx=ctx,
            err_msg="Failed to read password",
        )

        hostname = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter remote node host name", post_user_input_message="Selected remote hostname :: "
            ),
            ctx=ctx,
            err_msg="Failed to read hostname",
        )

        return SSHConnectionInfo(username, password, hostname, host_ip_address)

    def _run_ip_address_selection_flow(self, ip_discovery_range: str) -> str:
        if not self.checks.is_tool_exist_fn("nmap"):
            logger.warning("Missing mandatory utility. name: nmap")
            return None

        self.printer.print_with_rich_table_fn(generate_instructions_network_scan())
        scan_dict = self.network_util.get_all_lan_network_devices_fn(ip_range=ip_discovery_range, show_progress=True)
        self.printer.new_line_fn()

        options_dict: List[dict] = []
        for scan_item in scan_dict:
            options_dict.append(scan_dict[scan_item])

        selected_scanned_item: dict = self.prompter.prompt_user_selection_fn(
            message="Please choose a network device", options=options_dict
        )

        return selected_scanned_item["ip_address"] if selected_scanned_item is not None else None


def generate_instructions_network_scan() -> str:
    return f"""
  Required mandatory locally installed utility: [yellow]nmap[/yellow].
  [yellow]Elevated user permissions are required for this step ![/yellow]

  This step scans all devices on the LAN network and lists the following:

    • IP Address
    • Device Name
"""


def generate_instructions_connect_via_ssh(ip_address: str, user: str, password: str):
    return f"""
  Gathering SSH connection information for address [yellow]{ip_address}[/yellow].

  Requirements:
    • Ansible or Docker
      If Ansible is missing, a Docker image will be built and used instead.

  [yellow]This step prompts for connection access information (press ENTER for defaults):[/yellow]
    • Raspberry Pi node user     (default: [yellow]{user}[/yellow])
    • Raspberry Pi node password (default: [yellow]{password}[/yellow])

  To change the default values, please refer to the documentation.
"""


def generate_instructions_dhcpcd_config(ip_address: str, default_gw_address: str, default_dns_address: str):
    return f"""
  About to define a static IP via SSH on address [yellow]{ip_address}[/yellow].
  Subnet mask used for static IPs is xxx.xxx.xxx.xxx/24 (255.255.255.0).

  [red]Static IP address must be unique !
  Make sure it is not used anywhere else within LAN network or DHCP address pool range.[/red]

  Requirements:
    • Ansible or Docker
      If Ansible is missing, a Docker image will be built and used instead.

  This step requires the following values (press ENTER for defaults):
    • Raspberry Pi node desired static IP address
    • Raspberry Pi node desired hostname
    • Internet gateway address / home router address   (default: {default_gw_address})
    • Domain name server address / home router address (default: {default_dns_address})
"""
