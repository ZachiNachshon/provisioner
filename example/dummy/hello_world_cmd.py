#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from common.dummy.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
    HelloWorldRunnerCollaborators,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context


class HelloWorldCmdArgs:

    username: str
    node_username: str
    node_password: str
    ip_discovery_range: str

    def __init__(
        self,
        username: str = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
    ) -> None:

        self.username = username
        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range

    def print(self) -> None:
        logger.debug(
            f"HelloWorldCmdArgs: \n"
            + f"  username: {self.username}\n"
            + f"  node-username: {self.node_username}\n"
            + f"  node-password: REDACTED\n"
            + f"  ip-discovery-range: {self.ip_discovery_range}\n"
        )


class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldCmd run()")

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                username=args.username,
                node_username=args.node_username,
                node_password=args.node_password,
                ip_discovery_range=args.ip_discovery_range,
                ansible_playbook_path_hello_world="example/dummy/playbooks/hello_world.yaml",
            ),
            collaborators=HelloWorldRunnerCollaborators(ctx),
        )
