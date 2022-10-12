#!/usr/bin/env python3

import os

from typing import Optional
from loguru import logger
from rpi.os.domain.config import ProvisionerConfig
from common.remote.remote_network_configure import (
    RemoteMachineNetworkConfigureCollaborators,
    RemoteMachineNetworkConfigureRunner,
    RemoteMachineNetworkConfigureArgs,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.config.config_reader import ConfigReader
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "rpi/config.yaml"


class RPiNetworkConfigureArgs:

    node_username: str
    node_password: str
    ip_discovery_range: str
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str

    def __init__(
        self,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        gw_ip_address: Optional[str] = None,
        dns_ip_address: Optional[str] = None,
        static_ip_address: Optional[str] = None,
    ) -> None:

        self.node_username = node_username
        self.node_password = node_password
        self.ip_discovery_range = ip_discovery_range
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address

    def print(self) -> None:
        logger.debug(
            f"RPiOsConfigureArgs: \n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: REDACTED\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  gw_ip_address: {self.gw_ip_address}\n"
            + f"  dns_ip_address: {self.dns_ip_address}\n"
            + f"  static_ip_address: {self.static_ip_address}\n"
        )


class Collaborators:
    config_reader: ConfigReader


class RPiNetworkConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.yaml_util = YamlUtil.create(ctx, self.io)
        self.config_reader = ConfigReader.create(self.yaml_util)


class RPiNetworkConfigureRunner:
    def run(self, ctx: Context, args: RPiNetworkConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RPiNetworkConfigureRunner run()")

        config: ProvisionerConfig = collaborators.config_reader.read_config_fn(
            internal_path=CONFIG_INTERNAL_PATH, class_name=ProvisionerConfig, user_path=CONFIG_USER_PATH
        )

        node_username = config.node_username if args.node_username is None else args.node_username
        node_password = config.node_password if args.node_password is None else args.node_password
        ip_discovery_range = config.ip_discovery_range if args.ip_discovery_range is None else args.ip_discovery_range
        gw_ip_address = config.gw_ip_address if args.gw_ip_address is None else args.gw_ip_address
        dns_ip_address = config.dns_ip_address if args.dns_ip_address is None else args.dns_ip_address

        RemoteMachineNetworkConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineNetworkConfigureArgs(
                node_username=node_username,
                node_password=node_password,
                ip_discovery_range=ip_discovery_range,
                gw_ip_address=gw_ip_address,
                dns_ip_address=dns_ip_address,
                static_ip_address=args.static_ip_address,
                ansible_playbook_path_configure_network=config.ansible_playbook_path_configure_network,
                ansible_playbook_path_wait_for_network=config.ansible_playbook_path_wait_for_network,
            ),
            collaborators=RemoteMachineNetworkConfigureCollaborators(ctx),
        )
