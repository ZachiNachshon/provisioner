#!/usr/bin/env python3

import os
from typing import Optional

from loguru import logger

from common.remote.remote_network_configure import (
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureCollaborators,
    RemoteMachineNetworkConfigureRunner,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context


class RPiNetworkConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    ansible_playbook_path_configure_network: str = None
    ansible_playbook_path_wait_for_network: str = None

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        gw_ip_address: Optional[str] = None,
        dns_ip_address: Optional[str] = None,
        static_ip_address: Optional[str] = None,
        ansible_playbook_path_configure_network: Optional[str] = None,
        ansible_playbook_path_wait_for_network: Optional[str] = None,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.ansible_playbook_path_configure_network = ansible_playbook_path_configure_network
        self.ansible_playbook_path_wait_for_network = ansible_playbook_path_wait_for_network

    def print(self) -> None:
        logger.debug(
            f"RPiOsConfigureArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: REDACTED\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  gw_ip_address: {self.gw_ip_address}\n"
            + f"  dns_ip_address: {self.dns_ip_address}\n"
            + f"  static_ip_address: {self.static_ip_address}\n"
            + f"  ansible_playbook_path_configure_network: {self.ansible_playbook_path_configure_network}\n"
            + f"  ansible_playbook_path_wait_for_network: {self.ansible_playbook_path_wait_for_network}\n"
        )


class RPiNetworkConfigureRunner:
    def run(self, ctx: Context, args: RPiNetworkConfigureArgs) -> None:
        logger.debug("Inside RPiNetworkConfigureRunner run()")

        RemoteMachineNetworkConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineNetworkConfigureArgs(
                node_username=args.node_username,
                node_password=args.node_password,
                ip_discovery_range=args.ip_discovery_range,
                gw_ip_address=args.gw_ip_address,
                dns_ip_address=args.dns_ip_address,
                static_ip_address=args.static_ip_address,
                ansible_playbook_path_configure_network=args.ansible_playbook_path_configure_network,
                ansible_playbook_path_wait_for_network=args.ansible_playbook_path_wait_for_network,
            ),
            collaborators=RemoteMachineNetworkConfigureCollaborators(ctx),
        )
