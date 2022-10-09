#!/usr/bin/env python3

import os

from typing import Optional
from loguru import logger
from rpi.os.domain.config import ProvisionerConfig
from common.sd_card.remote_os_configure import (
    RemoteMachineConfigureCollaborators,
    RemoteMachineConfigureRunner,
    RemoteMachineConfigureArgs,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.config.config_reader import ConfigReader
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "rpi/config.yaml"


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
            + f"  node_username: {self.node_username}"
            + f"  node_password: REDACTED"
            + f"  ip_discovery_range: {self.ip_discovery_range}"
        )


class Collaborators:
    config_reader: ConfigReader


class RPiOsConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.yaml_util = YamlUtil.create(ctx, self.io)
        self.config_reader = ConfigReader.create(self.yaml_util)


class RPiOsConfigureRunner:
    def run(self, ctx: Context, args: RPiOsConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RpiOsConfigureRunner run()")

        config: ProvisionerConfig = collaborators.config_reader.read_config_fn(
            internal_path=CONFIG_INTERNAL_PATH, class_name=ProvisionerConfig, user_path=CONFIG_USER_PATH
        )

        node_username = config.node_username if args.node_username is None else args.node_username
        node_password = config.node_password if args.node_password is None else args.node_password
        ip_discovery_range = config.ip_discovery_range if args.ip_discovery_range is None else args.ip_discovery_range

        RemoteMachineConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineConfigureArgs(
                node_username, node_password, ip_discovery_range, config.ansible_playbook_file_path
            ),
            collaborators=RemoteMachineConfigureCollaborators(ctx),
        )
