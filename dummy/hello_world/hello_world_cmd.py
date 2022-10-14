#!/usr/bin/env python3

from typing import Optional
from loguru import logger
from common.dummy.hello_world_runner import (
    HelloWorldRunnerCollaborators,
    HelloWorldRunner,
    HelloWorldRunnerArgs,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context

class HelloWorldCmdArgs:

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
            f"HelloWorldCmdArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: REDACTED\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
        )

class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldRunner run()")

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                node_username="pi",
                node_password="raspberry",
                ip_discovery_range="192.168.1.1/24",
                ansible_playbook_path_hello_world="dummy/hello_world/playbooks/hello_world.yaml",
            ),
            collaborators=HelloWorldRunnerCollaborators(ctx),
        )
