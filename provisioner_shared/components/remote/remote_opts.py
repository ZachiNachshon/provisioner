#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

import click
from loguru import logger

from provisioner_shared.components.remote.domain.config import Auth, Host, RunEnvironment
from provisioner_shared.components.runtime.errors.cli_errors import MissingCliArgument
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsibleHost


class RemoteVerbosity(Enum):
    Normal = "Normal"
    Verbose = "Verbose"
    Silent = "Silent"

    @staticmethod
    def from_str(label):
        if label in ("Normal"):
            return RemoteVerbosity.Normal
        elif label in ("Verbose"):
            return RemoteVerbosity.Verbose
        elif label in ("Silent"):
            return RemoteVerbosity.Silent
        else:
            raise NotImplementedError(f"RemoteVerbosity enum does not support label '{label}'")


REMOTE_CLICK_CTX_NAME = "cli_remote_opts"


class CliRemoteOpts:

    def __init__(
        self,
        environment: Optional[RunEnvironment] = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        ip_address: Optional[str] = None,
        hostname: Optional[str] = None,
        # Hosts are not supplied via CLI arguments, only via user config
        remote_hosts: Optional[dict[str, Host]] = None,
        remote_context: RemoteContext = None,
    ) -> None:

        self.environment = environment
        self.node_username = node_username
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_discovery_range = ip_discovery_range
        self.ip_address = ip_address
        self.hostname = hostname

        # Calculated
        self.ansible_hosts = self._to_ansible_hosts(remote_hosts)

        # Modifiers
        self.remote_context = remote_context

    @staticmethod
    def from_click_ctx(ctx: click.Context) -> Optional["CliRemoteOpts"]:
        """Returns the current singleton instance, if any."""
        return ctx.obj.get(REMOTE_CLICK_CTX_NAME, None) if ctx.obj else None

    def get_remote_context(self) -> RemoteContext:
        return self.remote_context

    def _to_ansible_hosts(self, hosts: dict[str, Host]) -> List[AnsibleHost]:
        if not hosts:
            return None
        # In case IP address supplied as a CLI argument - flag or Env Var,
        # it'll be used as the sole remote machine
        if self.ip_address and len(str(self.ip_address)) > 0:
            # If using a one-liner command with IP address, all other auth flags must be supplied as well
            if (
                (not self.hostname and len(self.hostname) == 0)
                or (not self.ip_address and len(self.ip_address) == 0)
                or (not self.node_username and len(self.node_username) == 0)
            ):
                raise MissingCliArgument(
                    "When using ip-address flag, other remote flags become mandatory (hostname, node-username, node-password/ssh-private_key-file_path)"
                )
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
            for _, value in hosts.items():
                maybe_auth = value.auth if value.auth else Auth()
                # SSH private key can be supplied via CLI arguments or user config
                ssh_private_key_file_path = self.ssh_private_key_file_path if self.ssh_private_key_file_path else None
                if ssh_private_key_file_path is None and hasattr(maybe_auth, "ssh_private_key_file_path"):
                    ssh_private_key_file_path = maybe_auth.ssh_private_key_file_path
                result.append(
                    AnsibleHost(
                        host=value.name,
                        ip_address=value.address,
                        username=(self.node_username if self.node_username else maybe_auth.username),
                        password=(self.node_password if self.node_password else maybe_auth.password),
                        ssh_private_key_file_path=ssh_private_key_file_path,
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
