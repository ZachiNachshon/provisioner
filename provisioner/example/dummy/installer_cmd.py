#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger

from provisioner.common.anchor.anchor_runner import RunEnvironment
from provisioner.common.installer.installer_runner import (
    UtilityInstallerCmdRunner,
    UtilityInstallerCmdRunnerCollaborators,
    UtilityInstallerRunnerCmdArgs,
)
from provisioner.common.remote.remote_connector import RemoteCliArgs
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    HostIpPair,
)


class UtilityInstallerCmdArgs:

    utilities: List[str]
    environment: RunEnvironment
    github_access_token: str
    remote_args: RemoteCliArgs

    def __init__(
        self,
        utilities: List[str],
        environment: RunEnvironment,
        github_access_token: str,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        host_ip_pairs: List[HostIpPair] = None,
    ) -> None:

        self.remote_args = RemoteCliArgs(
            node_username, node_password, ip_discovery_range, host_ip_pairs, ssh_private_key_file_path
        )
        self.utilities = utilities
        self.environment = environment
        self.github_access_token = github_access_token

    def print(self) -> None:
        if self.remote_args:
            self.remote_args.print()
        logger.debug(
            f"InstallerCmdArgs: \n"
            + f"  utilities: {str(self.utilities)}\n"
            + f"  environment: {self.environment}\n"
            + f"  github_access_token: REDACTED\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> None:
        logger.debug("Inside UtilityInstallerCmd run()")

        UtilityInstallerCmdRunner().run(
            ctx=ctx,
            args=UtilityInstallerRunnerCmdArgs(
                utilities=args.utilities, github_access_token=args.github_access_token, remote_args=args.remote_args
            ),
            collaborators=UtilityInstallerCmdRunnerCollaborators(ctx),
            run_env=args.environment,
        )
