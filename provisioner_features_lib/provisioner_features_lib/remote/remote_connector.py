#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

from loguru import logger
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.runner.ansible.ansible_runner import AnsibleHost
from python_core_lib.shared.collaborators import CoreCollaborators

from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts


class NetworkDeviceSelectionMethod(str, Enum):
    ScanLAN = "Scan LAN"
    UserConfig = "User Config"
    UserPrompt = "User Prompt"


class NetworkDeviceAuthenticationMethod(str, Enum):
    Password = "Password"
    SSHPrivateKeyPath = "SSH Private Key"
    NoAuth = "No Auth"


class SSHConnectionInfo:
    ansible_hosts: List[AnsibleHost]

    def __init__(
        self,
        ansible_hosts: List[AnsibleHost],
    ) -> None:
        self.ansible_hosts = ansible_hosts


class DHCPCDConfigurationInfo:
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str

    def __init__(self, gw_ip_address: str, dns_ip_address: str, static_ip_address: str) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address


class RemoteMachineConnector:

    collaborators: CoreCollaborators = None

    def __init__(self, collaborators: CoreCollaborators) -> None:
        self.collaborators = collaborators

    def collect_ssh_connection_info(
        self,
        ctx: Context,
        remote_opts: Optional[CliRemoteOpts] = None,
        force_single_conn_info: Optional[bool] = False,
    ) -> SSHConnectionInfo:

        if ctx.is_dry_run():
            return SSHConnectionInfo(
                ansible_hosts=[
                    AnsibleHost(
                        host="DRY_RUN_RESPONSE",
                        ip_address="DRY_RUN_RESPONSE",
                        username="DRY_RUN_RESPONSE",
                        password="DRY_RUN_RESPONSE",
                        ssh_private_key_file_path="DRY_RUN_RESPONSE",
                    )
                ],
            )
        """
        Prompt the user for required remote SSH connection parameters
        Possible sources for host/IP pairs:
          - Scan local LAN network for available IP addresses
          - Use the hosts attribute from user configuration
          - Ask user for node host and IP address
        """
        selected_ansible_hosts: List[AnsibleHost] = []
        network_device_selection_method = self._ask_for_network_device_selection_method()

        if network_device_selection_method == NetworkDeviceSelectionMethod.UserConfig:
            selected_ansible_hosts = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: remote_opts
                and self._run_config_based_host_selection(
                    ansible_hosts=remote_opts.ansible_hosts, force_single_conn_info=force_single_conn_info
                ),
                ctx=ctx,
                err_msg="Failed to read host IP address from user configuration",
            )

        elif network_device_selection_method == NetworkDeviceSelectionMethod.ScanLAN:
            selected_ansible_hosts = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: remote_opts
                and self._run_scan_lan_host_selection(
                    ip_discovery_range=remote_opts.ip_discovery_range, force_single_conn_info=force_single_conn_info
                ),
                ctx=ctx,
                err_msg="Failed to read hosts IP addresses from LAN scan",
            )

        elif network_device_selection_method == NetworkDeviceSelectionMethod.UserPrompt:
            selected_ansible_hosts = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: self._run_manual_host_selection(ctx),
                ctx=ctx,
                err_msg="Failed to read a host IP address from user prompt",
            )
        else:
            return None

        return self._collect_ssh_auth_info(ctx=ctx, remote_opts=remote_opts, ansible_hosts=selected_ansible_hosts)

    def collect_dhcpcd_configuration_info(
        self,
        ctx: Context,
        ansible_hosts: str,
        static_ip_address: str = None,
        gw_ip_address: str = None,
        dns_ip_address: str = None,
    ) -> DHCPCDConfigurationInfo:

        self.collaborators.printer().print_with_rich_table_fn(
            generate_instructions_dhcpcd_config(
                ansible_hosts=ansible_hosts, default_gw_address=gw_ip_address, default_dns_address=dns_ip_address
            )
        )

        selected_static_ip = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                message="Enter a desired remote static IP address (example: 192.168.1.2XX)",
                default=static_ip_address,
                post_user_input_message="Selected remote static IP address       :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read static IP address",
        )

        selected_gw_address = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                message="Enter the gateway address",
                default=gw_ip_address,
                post_user_input_message="Selected gateway address                :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read gateway IP address",
        )

        selected_dns_resolver_address = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                message="Enter the DNS resolver address",
                default=dns_ip_address,
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

        network_device_select_method: str = self.collaborators.prompter().prompt_user_single_selection_fn(
            message="Please choose network device selection method", options=options_list
        )
        return NetworkDeviceSelectionMethod(network_device_select_method) if network_device_select_method else None

    def _ask_for_network_device_authentication_method(self) -> NetworkDeviceAuthenticationMethod:
        options_list: List[dict] = []
        for auth_method in NetworkDeviceAuthenticationMethod:
            options_list.append(auth_method.value)

        network_device_auth_method: str = self.collaborators.prompter().prompt_user_single_selection_fn(
            message="Please choose network device authentication method", options=options_list
        )
        return NetworkDeviceAuthenticationMethod(network_device_auth_method) if network_device_auth_method else None

    def _run_scan_lan_host_selection(self, ip_discovery_range: str, force_single_conn_info: bool) -> List[AnsibleHost]:
        if ip_discovery_range and len(ip_discovery_range) > 0:
            if self.collaborators.prompter().prompt_yes_no_fn(
                message=f"Scan LAN network for IP addresses at range {ip_discovery_range}",
                post_no_message="Skipped LAN network scan",
                post_yes_message=f"Selected to scan LAN at range {ip_discovery_range}",
            ):
                return self._run_lan_scan_host_selection(
                    ip_discovery_range=ip_discovery_range, force_single_conn_info=force_single_conn_info
                )
        return None

    def _run_manual_host_selection(self, ctx: Context) -> List[AnsibleHost]:
        ip_address = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                message="Enter remote node IP address",
                post_user_input_message="Selected IP address :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read node IP address",
        )

        hostname = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                message="Enter remote node host name",
                post_user_input_message="Selected remote hostname :: ",
            ),
            ctx=ctx,
            err_msg="Failed to read node host name",
        )

        return [AnsibleHost(host=hostname, ip_address=ip_address)]

    def _collect_ssh_auth_info(
        self,
        ctx: Context,
        remote_opts: CliRemoteOpts,
        ansible_hosts: List[AnsibleHost],
    ) -> SSHConnectionInfo:

        self.collaborators.printer().print_with_rich_table_fn(
            generate_instructions_connect_via_ssh(ansible_hosts=ansible_hosts)
        )

        for host in ansible_hosts:
            host.username = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                    message="Enter remote node user name",
                    default=remote_opts.node_username,
                    post_user_input_message="Selected remote user :: ",
                ),
                ctx=ctx,
                err_msg="Failed to read username",
            )

            auth_method = self._ask_for_network_device_authentication_method()

            if auth_method == NetworkDeviceAuthenticationMethod.Password:
                host.password = self._collect_auth_password(ctx, remote_opts)
            elif auth_method == NetworkDeviceAuthenticationMethod.SSHPrivateKeyPath:
                host.ssh_private_key_file_path = self._collect_auth_ssh_private_key_path(ctx, remote_opts)

        return SSHConnectionInfo(ansible_hosts=ansible_hosts)

    def _collect_auth_password(self, ctx: Context, remote_opts: CliRemoteOpts) -> str:
        password = None
        if remote_opts.node_password and len(remote_opts.node_password) > 0:
            password = remote_opts.node_password
            self.collaborators.printer().new_line_fn()
            self.collaborators.printer().print_fn("Identified SSH password from CLI argument.")
        else:
            password = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                    message="Enter remote node password",
                    default=remote_opts.node_password,
                    post_user_input_message="Set remote password :: ",
                    redact_value=True,
                ),
                ctx=ctx,
                err_msg="Failed to read password",
            )
        return password

    def _collect_auth_ssh_private_key_path(self, ctx: Context, remote_opts: CliRemoteOpts) -> str:
        ssh_private_key_path = None
        if remote_opts.ssh_private_key_file_path and len(remote_opts.ssh_private_key_file_path) > 0:
            ssh_private_key_path = remote_opts.ssh_private_key_file_path
            self.collaborators.printer().new_line_fn()
            self.collaborators.printer().print_fn("Identified SSH private key path from CLI argument.")
        else:
            ssh_private_key_path = Evaluator.eval_step_return_value_throw_on_failure(
                call=lambda: self.collaborators.prompter().prompt_user_input_fn(
                    message="Enter SSH private key path",
                    default=remote_opts.node_password,
                    post_user_input_message="Set private key path :: ",
                    redact_value=True,
                ),
                ctx=ctx,
                err_msg="Failed to read SSH private key path",
            )
        return ssh_private_key_path

    def _run_config_based_host_selection(
        self, ansible_hosts: List[AnsibleHost], force_single_conn_info: bool
    ) -> List[AnsibleHost]:

        if not ansible_hosts or len(ansible_hosts) == 0:
            return None

        options_list: List[str] = []
        option_to_value_dict: dict[str, dict] = {}
        for pair in ansible_hosts:
            identifier = f"{pair.host}, {pair.ip_address}"
            options_list.append(identifier)
            option_to_value_dict[identifier] = {"hostname": pair.host, "ip_address": pair.ip_address}

        return self._convert_prompted_host_selection_to_ansible_hosts(
            options_list=options_list,
            option_to_value_dict=option_to_value_dict,
            force_single_conn_info=force_single_conn_info,
        )

    def _run_lan_scan_host_selection(self, ip_discovery_range: str, force_single_conn_info: bool) -> List[AnsibleHost]:
        if not self.collaborators.checks().is_tool_exist_fn("nmap"):
            logger.error("Missing mandatory utility. name: nmap")
            return None

        self.collaborators.printer().print_with_rich_table_fn(generate_instructions_network_scan())
        scan_dict = self.collaborators.network_util().get_all_lan_network_devices_fn(
            ip_range=ip_discovery_range, show_progress=True
        )
        self.collaborators.printer().new_line_fn()

        options_list: List[str] = []
        option_to_value_dict: dict[str, dict] = {}
        for scan_item in scan_dict.values():
            identifier = f"{scan_item['hostname']}, {scan_item['ip_address']}"
            options_list.append(identifier)
            option_to_value_dict[identifier] = scan_item

        return self._convert_prompted_host_selection_to_ansible_hosts(
            options_list=options_list,
            option_to_value_dict=option_to_value_dict,
            force_single_conn_info=force_single_conn_info,
        )

    def _convert_prompted_host_selection_to_ansible_hosts(
        self, options_list: List[str], option_to_value_dict: dict[str, dict], force_single_conn_info: bool
    ) -> List[AnsibleHost]:

        result: List[AnsibleHost] = []
        if option_to_value_dict is None or len(option_to_value_dict) == 0:
            return result

        if force_single_conn_info:
            selected_item_from_config: dict = self.collaborators.prompter().prompt_user_single_selection_fn(
                message="Please choose a network device", options=options_list
            )
            selected_item_dict = option_to_value_dict[selected_item_from_config]
            result.append(AnsibleHost.from_dict(selected_item_dict))
        else:
            selected_items_from_config: dict = self.collaborators.prompter().prompt_user_multi_selection_fn(
                message="Please choose network devices", options=options_list
            )
            if selected_items_from_config and len(selected_items_from_config) > 0:
                for item in selected_items_from_config:
                    selected_item_dict = option_to_value_dict[item]
                    result.append(AnsibleHost.from_dict(selected_item_dict))
        return result


def generate_instructions_network_scan() -> str:
    return """
  Required mandatory locally installed utility: [yellow]nmap[/yellow].
  [yellow]Elevated user permissions are required for this step ![/yellow]

  This step scans all devices on the LAN network and lists the following:

    • IP Address
    • Device Name
"""


def generate_instructions_connect_via_ssh(ansible_hosts: List[AnsibleHost]):
    ip_addresses = ""
    if ansible_hosts:
        for pair in ansible_hosts:
            ip_addresses += f"    - [yellow]{pair.host}, {pair.ip_address}[/yellow]\n"

    return f"""
  Gathering SSH connection information for IP addresses:
{ip_addresses}
  This step prompts for connection access information (press ENTER for defaults):
    • Raspberry Pi node user
    • Raspberry Pi node password
    • Raspberry Pi private SSH key path (Recommended)

  To change the default values, please refer to the documentation.
  [yellow]It is recommended to use a SSH key instead of password for accessing remote machine.[/yellow]
"""


def generate_instructions_dhcpcd_config(
    ansible_hosts: List[AnsibleHost], default_gw_address: str, default_dns_address: str
):
    ip_addresses = ""
    if ansible_hosts:
        for pair in ansible_hosts:
            ip_addresses += f"    - [yellow]{pair.host}, {pair.ip_address}[/yellow]\n"

    return f"""
  About to define a static IP via SSH on address:
{ip_addresses}
  Subnet mask used for static IPs is xxx.xxx.xxx.xxx/24 (255.255.255.0).

  [red]Static IP address must be unique !
  Make sure it is not used anywhere else within LAN network or DHCP address pool range.[/red]

  This step requires the following values (press ENTER for defaults):
    • Single board node desired static IP address
    • Single board node desired hostname
    • Internet gateway address / home router address   (default: {default_gw_address})
    • Domain name server address / home router address (default: {default_dns_address})
"""
