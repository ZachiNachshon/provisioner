#!/usr/bin/env python3

import os

from typing import Optional
from loguru import logger
from rpi.os.domain.config import ProvisionerConfig
from common.remote.remote_os_configure import (
    RemoteMachineOsConfigureCollaborators,
    RemoteMachineOsConfigureRunner,
    RemoteMachineOsConfigureArgs,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.config.config_reader import ConfigReader
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "k3s/config.yaml"


class K3sMasterInstallArgs:

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
            f"K3sMasterInstallArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: REDACTED\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
        )


class Collaborators:
    config_reader: ConfigReader


class K3sMasterInstallCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.yaml_util = YamlUtil.create(ctx, self.io)
        self.config_reader = ConfigReader.create(self.yaml_util)


class K3sMasterInstallRunner:
    def run(self, ctx: Context, args: K3sMasterInstallArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside K3sMasterInstallRunner run()")

        config: ProvisionerConfig = collaborators.config_reader.read_config_fn(
            internal_path=CONFIG_INTERNAL_PATH, class_name=ProvisionerConfig, user_path=CONFIG_USER_PATH
        )

        node_username = config.node_username if args.node_username is None else args.node_username
        node_password = config.node_password if args.node_password is None else args.node_password
        ip_discovery_range = config.ip_discovery_range if args.ip_discovery_range is None else args.ip_discovery_range

        RemoteMachineOsConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineOsConfigureArgs(
                node_username=node_username,
                node_password=node_password,
                ip_discovery_range=ip_discovery_range,
                ansible_playbook_path_configure_os=config.ansible_playbook_path_configure_os,
            ),
            collaborators=RemoteMachineOsConfigureCollaborators(ctx),
        )
