#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

import click
from loguru import logger

from provisioner_shared.components.remote.domain.config import (
    Auth,
    Host,
    RemoteConfig,
    RemoteConnectMode,
    RunEnvironment,
)
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


class RemoteOptsFromScanFlags:
    def __init__(
        self,
        ip_discovery_range: Optional[str] = None,
    ) -> None:

        self.ip_discovery_range = ip_discovery_range

    def print(self) -> None:
        logger.debug("RemoteOptsFromScanFlags: \n" + f"  ip_discovery_range: {self.ip_discovery_range}\n")


class RemoteOptsFromConnFlags:

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_address: Optional[str] = None,
        port: Optional[int] = None,
        hostname: Optional[str] = None,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_address = ip_address
        self.port = port
        self.hostname = hostname

    def is_empty(self) -> bool:
        return not any(
            [
                self.node_username,
                self.node_password,
                self.ssh_private_key_file_path,
                self.ip_address,
                # self.port,
                self.hostname,
            ]
        )

    def get_ansible_hosts(self) -> List[AnsibleHost]:
        return [
            AnsibleHost(
                host=self.hostname,
                ip_address=self.ip_address,
                port=self.port,
                username=self.node_username,
                password=self.node_password,
                ssh_private_key_file_path=self.ssh_private_key_file_path,
            )
        ]

    def print(self) -> None:
        logger.debug(
            "RemoteOptsFromFlags: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: {self.node_password}\n"
            + f"  ip_address: {self.ip_address}\n"
            + f"  port: {self.port}\n"
            + f"  hostname: {self.hostname}\n"
            + f"  ssh_private_key_file_path: {self.ssh_private_key_file_path}\n",
        )


class RemoteOptsFromConfig:

    def __init__(self, remote_config: Optional[RemoteConfig] = None):
        self._remote_cfg_dict: dict[str, Host] = remote_config.to_hosts_dict()

    def print(self) -> None:
        logger.debug(
            "RemoteOptsFromConfig: \n"
            + f"  ansible_hosts: {'read from user config' if self._remote_cfg_dict is not None else None}\n"
        )

    def get_ansible_hosts(self) -> List[AnsibleHost]:
        if not self._remote_cfg_dict:
            return None

        result: List[AnsibleHost] = []
        for _, value in self._remote_cfg_dict.items():
            maybe_auth = value.auth if value.auth else Auth()
            # print(f"maybe_auth: {maybe_auth.__dict__}")
            result.append(
                AnsibleHost(
                    host=value.name,
                    ip_address=value.address,
                    port=value.port,
                    username=maybe_auth.username,
                    password=maybe_auth.password,
                    ssh_private_key_file_path=maybe_auth.ssh_private_key_file_path,
                )
            )
        return result


class RemoteOpts:

    def __init__(
        self,
        remote_context: RemoteContext = None,
        environment: Optional[RunEnvironment] = None,
        connect_mode: Optional[RemoteConnectMode] = None,
        conn_flags: RemoteOptsFromConnFlags = None,
        scan_flags: RemoteOptsFromScanFlags = None,
        config: RemoteOptsFromConfig = None,
    ) -> None:
        # Modifiers
        self._remote_context = remote_context
        self._environment = environment
        self._connect_mode = connect_mode
        self._conn_flags = conn_flags
        self._scan_flags = scan_flags
        self._config = config

    @staticmethod
    def from_click_ctx(ctx: click.Context) -> Optional["RemoteOpts"]:
        """Returns the current singleton instance, if any."""
        return ctx.obj.get(REMOTE_CLICK_CTX_NAME, None) if ctx.obj else None

    def get_remote_context(self) -> RemoteContext:
        return self._remote_context

    def get_environment(self) -> RunEnvironment:
        return self._environment

    def get_connect_mode(self) -> RemoteConnectMode:
        return self._connect_mode

    def get_conn_flags(self) -> RemoteOptsFromConnFlags:
        return self._conn_flags

    def get_scan_flags(self) -> RemoteOptsFromScanFlags:
        return self._scan_flags

    def get_config(self) -> RemoteOptsFromConfig:
        return self._config

    def print(self) -> None:
        logger.debug(
            "RemoteOpts: \n"
            + f"  environment: {self._environment}\n"
            + f"  connect_mode: {self._connect_mode}\n"
            + f"  remote_context: {str(self._remote_context.__dict__) if self._remote_context is not None else None}\n"
        )
        if self._conn_flags:
            self._conn_flags.print()
        if self._config:
            self._config.print()
        if self._scan_flags:
            self._scan_flags.print()
