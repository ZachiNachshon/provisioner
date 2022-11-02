#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from common.remote.remote_connector import RemoteCliArgs

from common.remote.remote_network_configure import (
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureCollaborators,
    RemoteMachineNetworkConfigureRunner,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import HostIpPair

RemoteMachineNetworkAnsiblePlaybookPath = "rpi/os/playbooks/configure_network.yaml"

class RPiNetworkConfigureCmdArgs:

    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    remote_args: RemoteCliArgs

    def __init__(
        self,
        gw_ip_address: Optional[str] = None,
        dns_ip_address: Optional[str] = None,
        static_ip_address: Optional[str] = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        host_ip_pairs: List[HostIpPair] = None,
    ) -> None:
        self.remote_args = RemoteCliArgs(node_username, node_password, ip_discovery_range, host_ip_pairs, ssh_private_key_file_path)
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address

    def print(self) -> None:
        if self.remote_args: 
            self.remote_args.print()
        logger.debug(
            f"RPiNetworkConfigureCmdArgs: \n"
            + f"  gw_ip_address: {self.gw_ip_address}\n"
            + f"  dns_ip_address: {self.dns_ip_address}\n"
            + f"  static_ip_address: {self.static_ip_address}\n"
        )


class RPiNetworkConfigureCmd:
    def run(self, ctx: Context, args: RPiNetworkConfigureCmdArgs) -> None:
        logger.debug("Inside RPiNetworkConfigureCmd run()")

        RemoteMachineNetworkConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineNetworkConfigureArgs(
                remote_args=args.remote_args,
                gw_ip_address=args.gw_ip_address,
                dns_ip_address=args.dns_ip_address,
                static_ip_address=args.static_ip_address,
                ansible_playbook_path_configure_network=RemoteMachineNetworkAnsiblePlaybookPath,
            ),
            collaborators=RemoteMachineNetworkConfigureCollaborators(ctx),
        )
