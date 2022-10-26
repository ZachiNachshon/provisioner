#!/usr/bin/env python3

import os
from typing import Optional

import typer
from loguru import logger

from config.config_resolver import ConfigResolver
from config.typer_remote_opts import TyperRemoteOpts
from external.python_scripts_lib.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import (
    CliContextManager,
)
from rpi.os.configure import RPiOsConfigureArgs, RPiOsConfigureRunner
from rpi.os.install import RPiOsInstallCmd, RPiOsInstallCmdArgs
from rpi.os.network import RPiNetworkConfigureArgs, RPiNetworkConfigureRunner

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "rpi/config.yaml"

ConfigResolver.resolve(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH)
TyperRemoteOpts.load(ConfigResolver.config)

os_cli_app = typer.Typer()


@os_cli_app.command(name="install")
@logger.catch(reraise=True)
def install(
    image_download_url: Optional[str] = typer.Option(
        ConfigResolver.get_config().get_os_raspbian_download_url(),
        help="OS image file download URL",
        envvar="IMAGE_DOWNLOAD_URL",
    )
) -> None:
    """
    Select an available SD-CARD to burn a Raspbian OS image
    """
    try:
        args = RPiOsInstallCmdArgs(
            image_download_url=image_download_url
        )
        args.print()
        RPiOsInstallCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


@os_cli_app.command(name="configure")
@logger.catch(reraise=True)
def configure(
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
    Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
    """
    try:
        args = RPiOsConfigureArgs(
            node_username=node_username,
            node_password=node_password,
            ip_discovery_range=ip_discovery_range,
        )
        args.print()
        RPiOsConfigureRunner().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


@os_cli_app.command(name="network")
@logger.catch(reraise=True)
def network(
    static_ip_address: Optional[str] = typer.Option(
        ..., help="Static IP address to set as the remote host IP address", envvar="RPI_STATIC_IP"
    ),
    gw_ip_address: Optional[str] = typer.Option(
        TyperRemoteOpts.config.rpi.network.gw_ip_address,
        help="Internet gateway address / home router address",
        envvar="GATEWAY_ADDRESS",
    ),
    dns_ip_address: Optional[str] = typer.Option(
        TyperRemoteOpts.config.rpi.network.dns_ip_address,
        help="Domain name server address / home router address",
        envvar="DNS_ADDRESS",
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
    """
    try:
        args = RPiNetworkConfigureArgs(
            node_username=node_username,
            node_password=node_password,
            ip_discovery_range=ip_discovery_range,
            gw_ip_address=gw_ip_address,
            dns_ip_address=dns_ip_address,
            static_ip_address=static_ip_address,
        )
        args.print()
        RPiNetworkConfigureRunner().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
