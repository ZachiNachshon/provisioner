#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

from loguru import logger

from provisioner.config.domain.config import RemoteConfig
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from provisioner.external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    HostIpPair,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter


class NetworkDeviceSelectionMethod(str, Enum):
    ScanLAN = "Scan LAN"
    UserConfig = "User Config"
    UserPrompt = "User Prompt"


class RemoteCliArgs:
    node_username: str
    node_password: str
    ip_discovery_range: str
    host_ip_pairs: List[HostIpPair]
    ssh_private_key_file_path: str

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        host_ip_pairs: Optional[List[HostIpPair]] = None,
        ssh_private_key_file_path: Optional[str] = None,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.host_ip_pairs = host_ip_pairs
        self.ssh_private_key_file_path = ssh_private_key_file_path

    @staticmethod
    def to_host_ip_pairs(hosts: dict[str, RemoteConfig.Host]) -> List[HostIpPair]:
        if not hosts:
            return None
        result: List[HostIpPair] = []
        for key, value in hosts.items():
            result.append(HostIpPair(value.name, value.address))
        return result

    def print(self) -> None:
        logger.debug(
            f"RemoteCliArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: {self.node_password}\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  host_ip_pairs: {'supplied via CLI arguments or user config' if self.host_ip_pairs is not None else None}\n"
            + f"  ssh_private_key_file_path: {self.ssh_private_key_file_path}\n"
        )


class SSHConnectionInfo:
    username: str
    password: str
    ssh_private_key_file_path: str
    host_ip_pairs: List[HostIpPair]

    def __init__(
        self,
        username: str,
        host_ip_pairs: List[HostIpPair],
        password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
    ) -> None:

        self.username = username
        self.password = password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.host_ip_pairs = host_ip_pairs


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
        remote_args: Optional[RemoteCliArgs] = None,
        force_single_conn_info: Optional[bool] = False,
    ) -> SSHConnectionInfo:

        if ctx.is_dry_run():
            return SSHConnectionInfo(
                username="DRY_RUN_RESPONSE",
                password="DRY_RUN_RESPONSE",
                ssh_private_key_file_path="DRY_RUN_RESPONSE",
                host_ip_pairs=[],
            )

        """
        Prompt the user for required remote SSH connection parameters
        Possible sources for host/IP pairs:
          - Scan local LAN network for available IP addresses
          - Use the hosts attribute from user configuration
          - Ask user for node host and IP address
        """
        selected_host_ip_pairs: List[HostIpPair] = []
        network_device_selection_method = self._ask_for_network_device_selection_method()

        if network_device_selection_method == NetworkDeviceSelectionMethod.UserConfig:
            selected_host_ip_pairs = Evaluator.eval_step_failure_throws(
                call=lambda: remote_args
                and self._select_from_existing_host_ip_pairs(remote_args.host_ip_pairs, force_single_conn_info),
                ctx=ctx,
                err_msg="Failed to read host IP address from user configuration",
            )

        elif network_device_selection_method == NetworkDeviceSelectionMethod.ScanLAN:
            selected_host_ip_pairs = Evaluator.eval_step_failure_throws(
                call=lambda: remote_args
                and self._run_host_ip_address_scan(remote_args.ip_discovery_range, force_single_conn_info),
                ctx=ctx,
                err_msg="Failed to read host IP address from LAN scan",
            )

        elif network_device_selection_method == NetworkDeviceSelectionMethod.UserPrompt:
            selected_host_ip_pairs = Evaluator.eval_step_failure_throws(
                call=lambda: self._run_single_host_ip_selection_flow(),
                ctx=ctx,
                err_msg="Failed to read a host IP address from user prompt",
            )
        else:
            return None

        return self._get_ssh_connection_info(ctx, remote_args, selected_host_ip_pairs)

    def collect_dhcpcd_configuration_info(
        self, ctx: Context, host_ip_pairs: str, arg_static_ip: str, arg_gw_address: str, arg_dns_address: str
    ) -> DHCPCDConfigurationInfo:

        self.printer.print_with_rich_table_fn(
            generate_instructions_dhcpcd_config(
                host_ip_pairs=host_ip_pairs, default_gw_address=arg_gw_address, default_dns_address=arg_dns_address
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

    def _ask_for_network_device_selection_method(self) -> NetworkDeviceSelectionMethod:
        options_list: List[dict] = []
        for sel_method in NetworkDeviceSelectionMethod:
            options_list.append(sel_method.value)

        network_device_select_method: str = self.prompter.prompt_user_selection_fn(
            message="Please choose network device selection method", options=options_list
        )
        return NetworkDeviceSelectionMethod(network_device_select_method) if network_device_select_method else None

    def _run_host_ip_address_scan(self, ip_discovery_range: str, force_single_conn_info: bool) -> List[HostIpPair]:
        if ip_discovery_range and len(ip_discovery_range) > 0:
            if self.prompter.prompt_yes_no_fn(
                message=f"Scan LAN network for IP addresses at range {ip_discovery_range}",
                post_no_message="Skipped LAN network scan",
                post_yes_message=f"Selected to scan LAN at range {ip_discovery_range}",
            ):
                return self._run_lan_scan_selection_flow(ip_discovery_range, force_single_conn_info)
        return None

    def _run_single_host_ip_selection_flow(self) -> List[HostIpPair]:
        single_ip_address = self.prompter.prompt_user_input_fn(
            message="Enter remote node IP address", post_user_input_message="Selected IP address :: "
        )
        single_hostname = self.prompter.prompt_user_input_fn(
            message="Enter remote node host name", post_user_input_message="Selected remote hostname :: "
        )
        return (
            [HostIpPair(host=single_hostname, ip_address=single_ip_address)]
            if len(single_hostname) > 0 and len(single_hostname) > 0
            else None
        )

    def _get_ssh_connection_info(
        self,
        ctx: Context,
        remote_args: RemoteCliArgs,
        selected_host_ip_pairs: List[HostIpPair],
    ) -> SSHConnectionInfo:

        self.printer.print_with_rich_table_fn(
            generate_instructions_connect_via_ssh(host_ip_pairs=selected_host_ip_pairs)
        )

        username = Evaluator.eval_step_failure_throws(
            call=lambda: self.prompter.prompt_user_input_fn(
                message="Enter remote node user",
                default=remote_args.node_username,
                post_user_input_message="Selected remote user :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read username",
        )

        if remote_args.ssh_private_key_file_path and len(remote_args.ssh_private_key_file_path) > 0:
            self.printer.new_line_fn()
            self.printer.print_fn("Identified SSH private key path in user configuration, skipping password prompt.")
            return SSHConnectionInfo(
                username=username,
                ssh_private_key_file_path=remote_args.ssh_private_key_file_path,
                host_ip_pairs=selected_host_ip_pairs,
            )

            # TODO: might want to avoid from prompting for auth method since Ansible SSH key in keychain is used by default
        else:
            password = Evaluator.eval_step_failure_throws(
                call=lambda: self.prompter.prompt_user_input_fn(
                    message="Enter remote node password",
                    default=remote_args.node_password,
                    post_user_input_message="Selected remote password :: ",
                    redact_default=True,
                ),
                ctx=ctx,
                err_msg="Failed to read password",
            )
            return SSHConnectionInfo(username=username, password=password, host_ip_pairs=selected_host_ip_pairs)

    def _select_from_existing_host_ip_pairs(
        self, host_ip_pairs: List[HostIpPair], force_single_conn_info: bool
    ) -> List[HostIpPair]:

        if not host_ip_pairs or len(host_ip_pairs) == 0:
            return None

        options_list: List[str] = []
        option_to_value_map: dict[str, dict] = {}
        for pair in host_ip_pairs:
            identifier = f"{pair.host}, {pair.ip_address}"
            options_list.append(identifier)
            option_to_value_map[identifier] = {"hostname": pair.host, "ip_address": pair.ip_address}

        result: List[HostIpPair] = []
        if force_single_conn_info:
            selected_scanned_items: dict = self.prompter.prompt_user_selection_fn(
                message="Please choose a network device", options=options_list
            )
            selected_item_dict = option_to_value_map[selected_scanned_items]
            result.append(HostIpPair(host=selected_item_dict["hostname"], ip_address=selected_item_dict["ip_address"]))
        else:
            selected_scanned_items: dict = self.prompter.prompt_user_multi_selection_fn(
                message="Please choose a network device", options=options_list
            )
            if selected_scanned_items and len(selected_scanned_items) > 0:
                for item in selected_scanned_items:
                    selected_item_dict = option_to_value_map[item]
                    result.append(
                        HostIpPair(host=selected_item_dict["hostname"], ip_address=selected_item_dict["ip_address"])
                    )

        return result

    def _run_lan_scan_selection_flow(self, ip_discovery_range: str, force_single_conn_info: bool) -> List[HostIpPair]:
        if not self.checks.is_tool_exist_fn("nmap"):
            logger.warning("Missing mandatory utility. name: nmap")
            return None

        self.printer.print_with_rich_table_fn(generate_instructions_network_scan())
        scan_dict = self.network_util.get_all_lan_network_devices_fn(ip_range=ip_discovery_range, show_progress=True)
        self.printer.new_line_fn()

        options_list: List[str] = []
        option_to_value_map: dict[str, dict] = {}
        for scan_item in scan_dict.values():
            identifier = f"{scan_item['hostname']}, {scan_item['ip_address']}"
            options_list.append(identifier)
            option_to_value_map[identifier] = scan_item

        result: List[HostIpPair] = []
        if force_single_conn_info:
            selected_scanned_items: dict = self.prompter.prompt_user_selection_fn(
                message="Please choose a network device", options=options_list
            )
            selected_item_dict = option_to_value_map[selected_scanned_items]
            result.append(HostIpPair(host=selected_item_dict["hostname"], ip_address=selected_item_dict["ip_address"]))
        else:
            selected_scanned_items: dict = self.prompter.prompt_user_multi_selection_fn(
                message="Please choose a network device", options=options_list
            )
            if selected_scanned_items and len(selected_scanned_items) > 0:
                for item in selected_scanned_items:
                    selected_item_dict = option_to_value_map[item]
                    result.append(
                        HostIpPair(host=selected_item_dict["hostname"], ip_address=selected_item_dict["ip_address"])
                    )

        return result


def generate_instructions_network_scan() -> str:
    return f"""
  Required mandatory locally installed utility: [yellow]nmap[/yellow].
  [yellow]Elevated user permissions are required for this step ![/yellow]

  This step scans all devices on the LAN network and lists the following:

    • IP Address
    • Device Name
"""


def generate_instructions_connect_via_ssh(host_ip_pairs: List[HostIpPair]):
    ip_addresses = ""
    if host_ip_pairs:
        for pair in host_ip_pairs:
            ip_addresses += f"    - [yellow]{pair.host}, {pair.ip_address}[/yellow]\n"

    return f"""
  Gathering SSH connection information for IP addresses:
{ip_addresses}
  Requirements:
    • Ansible or Docker
      If Ansible is missing, a Docker image will be built and used instead.

  This step prompts for connection access information (press ENTER for defaults):
    • Raspberry Pi node user
    • Raspberry Pi node password
    • Raspberry Pi private SSH key path (Recommended)

  To change the default values, please refer to the documentation.
  [yellow]It is recommended to use SSH key instead of password for accessing remote machine.[/yellow]
"""


def generate_instructions_dhcpcd_config(
    host_ip_pairs: List[HostIpPair], default_gw_address: str, default_dns_address: str
):
    ip_addresses = ""
    if host_ip_pairs:
        for pair in host_ip_pairs:
            ip_addresses += f"    - [yellow]{pair.host}, {pair.ip_address}[/yellow]\n"

    return f"""
  About to define a static IP via SSH on address:
{ip_addresses}  
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
