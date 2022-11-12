#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger

from provisioner.common.dummy.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
    HelloWorldRunnerCollaborators,
)
from provisioner.common.remote.remote_connector import RemoteCliArgs
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    HostIpPair,
)


class HelloWorldCmdArgs:

    username: str
    remote_args: RemoteCliArgs

    def __init__(
        self,
        username: str = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        host_ip_pairs: List[HostIpPair] = None,
    ) -> None:

        self.remote_args = RemoteCliArgs(
            node_username, node_password, ip_discovery_range, host_ip_pairs, ssh_private_key_file_path
        )
        self.username = username

    def print(self) -> None:
        if self.remote_args:
            self.remote_args.print()
        logger.debug(f"HelloWorldCmdArgs: \n" + f"  username: {self.username}\n")


class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldCmd run()")

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                username=args.username,
                remote_args=args.remote_args,
            ),
            collaborators=HelloWorldRunnerCollaborators(ctx),
        )
