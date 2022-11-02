#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from common.remote.remote_connector import RemoteCliArgs

from common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureCollaborators,
    RemoteMachineOsConfigureRunner,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import HostIpPair

RemoteMachineOsConfigureAnsiblePlaybookPath = "rpi/os/playbooks/configure_os.yaml"

class RPiOsConfigureCmdArgs:

    remote_args: RemoteCliArgs

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        host_ip_pairs: List[HostIpPair] = None,
    ) -> None:

        self.remote_args = RemoteCliArgs(node_username, node_password, ip_discovery_range, host_ip_pairs, ssh_private_key_file_path)

    def print(self) -> None:
        if self.remote_args: 
            self.remote_args.print()
        logger.debug(
            "RPiOsConfigureCmdArgs: \n"
        )


class RPiOsConfigureCmd:
    def run(self, ctx: Context, args: RPiOsConfigureCmdArgs) -> None:
        logger.debug("Inside RPiOsConfigureCmd run()")

        RemoteMachineOsConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineOsConfigureArgs(
                remote_args=args.remote_args,
                ansible_playbook_path_configure_os=RemoteMachineOsConfigureAnsiblePlaybookPath,
            ),
            collaborators=RemoteMachineOsConfigureCollaborators(ctx),
        )
