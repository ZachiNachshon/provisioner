#!/usr/bin/env python3

import typer
from loguru import logger

from external.python_scripts_lib.python_scripts_lib.config.config_reader import (
    ConfigReader,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from rpi.os.domain.config import ProvisionerConfig


class TyperRemoteOpts:

    # Static variable
    config: ProvisionerConfig

    @staticmethod
    def load(config: ProvisionerConfig) -> None:
        TyperRemoteOpts.config = config

    def node_username():
        return typer.Option(
            TyperRemoteOpts.config.node_username, help="(Remote only) Remote node username", envvar="NODE_USERNAME"
        )

    def node_password():
        return typer.Option(
            TyperRemoteOpts.config.node_password, help="(Remote only) Remote node password", envvar="NODE_PASSWORD"
        )

    def ip_discovery_range():
        return typer.Option(
            TyperRemoteOpts.config.ip_discovery_range,
            help="(Remote only) LAN network IP discovery range",
            envvar="IP_DISCOVERY_RANGE",
        )

    def gw_ip_address():
        return typer.Option(
            TyperRemoteOpts.config.gw_ip_address,
            help="(Remote only) Internet gateway address / home router address",
            envvar="GATEWAY_ADDRESS",
        )

    def dns_ip_address():
        return typer.Option(
            TyperRemoteOpts.config.dns_ip_address,
            help="(Remote only) Domain name server address / home router address",
            envvar="DNS_ADDRESS",
        )
