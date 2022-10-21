#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureCollaborators,
    RemoteMachineOsConfigureRunner,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context

RemoteMachineOsConfigureAnsiblePlaybookPath = "rpi/os/playbooks/configure_os.yaml"

class RPiOsConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range

    def print(self) -> None:
        logger.debug(
            f"RPiOsConfigureArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: REDACTED\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
        )


class RPiOsConfigureRunner:
    def run(self, ctx: Context, args: RPiOsConfigureArgs) -> None:
        logger.debug("Inside RpiOsConfigureRunner run()")

        RemoteMachineOsConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineOsConfigureArgs(
                node_username=args.node_username,
                node_password=args.node_password,
                ip_discovery_range=args.ip_discovery_range,
                ansible_playbook_path_configure_os=RemoteMachineOsConfigureAnsiblePlaybookPath,
            ),
            collaborators=RemoteMachineOsConfigureCollaborators(ctx),
        )
