#!/usr/bin/env python3

from typing import List, Optional

from provisioner.errors.cli_errors import MissingCliArgument
import typer
from loguru import logger
from provisioner.cli.typer_callbacks import exclusivity_callback
from provisioner.infra.remote_context import RemoteContext
from provisioner.runner.ansible.ansible_runner import AnsibleHost

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment

REMOTE_ONLY_HELP_TITLE = "Remote Only"


class TyperRemoteOpts:

    _remote_config: RemoteConfig = None
    _cli_remote_opts: "CliRemoteOpts" = None

    def __init__(self, remote_config: RemoteConfig = None) -> None:
        self._remote_config = remote_config

    def environment(self):
        return typer.Option(
            None,
            show_default=False,
            help="Specify an environment or select from a list if none supplied",
            envvar="PROV_RUN_ENVIRONMENT",
        )

    def node_username(self):
        return typer.Option(
            None,
            show_default=False,
            help="Remote node username",
            envvar="PROV_NODE_USERNAME",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def node_password(self):
        return typer.Option(
            None,
            show_default=False,
            help="Remote node password",
            envvar="PROV_NODE_PASSWORD",
            callback=exclusivity_callback,
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def ssh_private_key_file_path(self):
        return typer.Option(
            None,
            show_default=False,
            help="Private SSH key local file path",
            envvar="PROV_SSH_PRIVATE_KEY_FILE_PATH",
            callback=exclusivity_callback,
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def ip_discovery_range(self, from_config: str = None):
        return typer.Option(
            default=from_config,
            help="LAN network IP discovery scan range",
            envvar="PROV_IP_DISCOVERY_RANGE",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )
    
    def ip_address(self):
        return typer.Option(
            default="",
            help="Remote node IP address",
            envvar="PROV_IP_ADDRESS",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )
    
    def hostname(self):
        return typer.Option(
            default="",
            help="Remote node host name",
            envvar="PROV_HOSTNAME",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )
    
    def dry_run(self):
        return typer.Option(
            False,
            "--dry-run",
            "-d",
            is_flag=True,
            show_default=True,
            help="[Remote Machine] Run command as NO-OP, print commands to output, do not execute",
            envvar="PROV_REMOTE_DRY_RUN",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def verbose(self):
        return typer.Option(
            False,
            "--verbose",
            "-v",
            is_flag=True,
            show_default=True,
            help="[Remote Machine] Run command with DEBUG verbosity",
            envvar="REMOTE_VERBOSE",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def silent(self):
        return typer.Option(
            False,
            "--silent",
            "-s",
            is_flag=True,
            show_default=True,
            help="[Remote Machine] Suppress log output",
            envvar="PROV_REMOTE_SILENT",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def non_interactive(self):
        return typer.Option(
            False,
            "--non-interactive",
            "-n",
            is_flag=True,
            show_default=True,
            help="[Remote Machine] Turn off interactive prompts and outputs",
            envvar="PROV_REMOTE_NON_INTERACTIVE",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    def as_typer_callback(self):
        from_cfg_ip_discovery_range = None
        if self._remote_config is not None and self._remote_config.lan_scan is not None:
            from_cfg_ip_discovery_range = self._remote_config.lan_scan.ip_discovery_range

        def typer_callback(
            environment: RunEnvironment = self.environment(),
            node_username: Optional[str] = self.node_username(),
            node_password: Optional[str] = self.node_password(),
            ssh_private_key_file_path: Optional[str] = self.ssh_private_key_file_path(),
            ip_discovery_range: Optional[str] = self.ip_discovery_range(from_cfg_ip_discovery_range),
            ip_address: Optional[str] = self.ip_address(),
            hostname: Optional[str] = self.hostname(),
            dry_run: Optional[bool] = self.dry_run(),
            verbose: Optional[bool] = self.verbose(),
            silent: Optional[bool] = self.silent(),
            non_interactive: Optional[bool] = self.non_interactive(),
        ):

            remote_context = RemoteContext.create(
                dry_run=dry_run,
                verbose=verbose,
                silent=silent,
                non_interactive=non_interactive,
            )
            self._cli_remote_opts = CliRemoteOpts(
                environment=environment,
                node_username=node_username,
                node_password=node_password,
                ssh_private_key_file_path=ssh_private_key_file_path,
                ip_discovery_range=ip_discovery_range,
                ip_address=ip_address,
                hostname=hostname,
                # Hosts are not supplied via CLI arguments, only via user config
                remote_hosts=self._remote_config.hosts,
                remote_context=remote_context,
            )

        return typer_callback

    def to_cli_opts(self) -> "CliRemoteOpts":
        return self._cli_remote_opts


class CliRemoteOpts:

    environment: Optional[RunEnvironment]
    node_username: Optional[str]
    node_password: Optional[str]
    ssh_private_key_file_path: Optional[str]
    ip_discovery_range: Optional[str]
    ip_address: Optional[str]
    hostname: Optional[str]

    # Calculated
    ansible_hosts: List[AnsibleHost]

    # Modifiers
    remote_context: RemoteContext

    def __init__(
        self,
        environment: Optional[RunEnvironment] = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        ip_address: Optional[str] = None,
        hostname: Optional[str] = None,
        remote_hosts: Optional[dict[str, RemoteConfig.Host]] = None,
        remote_context: RemoteContext = None,
    ) -> None:

        self.environment = environment
        self.node_username = node_username
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_discovery_range = ip_discovery_range
        self.ip_address = ip_address
        self.hostname = hostname
        self.ansible_hosts = self._to_ansible_hosts(remote_hosts)
        self.remote_context = remote_context

    def get_remote_context(self) -> RemoteContext:
        return self.remote_context

    def _to_ansible_hosts(self, hosts: dict[str, RemoteConfig.Host]) -> List[AnsibleHost]:
        if not hosts:
            return None
        # In case IP address supplied as a CLI argument - flag or Env Var,
        # it'll be used as the sole remote machine
        if self.ip_address and len(str(self.ip_address)) > 0:
            # If using a one-liner command with IP address, all other auth flags must be supplied as well
            if (not self.hostname and len(self.hostname) == 0) or \
                (not self.ip_address and len(self.ip_address) == 0) or \
                (not self.node_username and len(self.node_username) == 0):
                raise MissingCliArgument("When using ip-address flag, other remote flags become mandatory (hostname, node-username, node-password/ssh-private_key-file_path)")
            return [
                AnsibleHost(
                    host=self.hostname,
                    ip_address=self.ip_address,
                    username=self.node_username,
                    password=self.node_password,
                    ssh_private_key_file_path=self.ssh_private_key_file_path,
                )
            ]
        else:
            result: List[AnsibleHost] = []
            for key, value in hosts.items():
                # If user supplied remote options via CLI arguments - override all other sources
                result.append(
                    AnsibleHost(
                        host=value.name,
                        ip_address=value.address,
                        username=self.node_username if self.node_username else value.auth.username,
                        password=self.node_password if self.node_password else value.auth.password,
                        ssh_private_key_file_path=self.ssh_private_key_file_path
                        if self.ssh_private_key_file_path
                        else value.auth.ssh_private_key_file_path,
                    )
                )
            return result

    def print(self) -> None:
        logger.debug(
            "CliRemoteOpts: \n"
            + f"  remote_context: {str(self.remote_context.__dict__) if self.remote_context is not None else None}\n"
            + f"  environment: {self.environment}\n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: {self.node_password}\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  ip_address: {self.ip_address}\n"
            + f"  hostname: {self.hostname}\n"
            + f"  ssh_private_key_file_path: {self.ssh_private_key_file_path}\n"
            + f"  ansible_hosts: {'supplied via CLI arguments or user config' if self.ansible_hosts is not None else None}\n"
        )
