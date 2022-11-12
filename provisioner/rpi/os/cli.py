#!/usr/bin/env python3

import os
import pathlib
import pkgutil
from typing import Optional

import typer
from loguru import logger

from provisioner.common.remote.remote_connector import RemoteCliArgs
from provisioner.config.config_resolver import ConfigResolver
from provisioner.config.typer_remote_opts import TyperRemoteOpts
from provisioner.external.python_scripts_lib.python_scripts_lib.cli.state import CliGlobalArgs
from provisioner.external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import (
    CliContextManager,
)
from provisioner.rpi.os.burn_image_cmd import RPiOsBurnImageCmd, RPiOsBurnImageCmdArgs
from provisioner.rpi.os.configure_cmd import RPiOsConfigureCmd, RPiOsConfigureCmdArgs
from provisioner.rpi.os.network_cmd import RPiNetworkConfigureCmd, RPiNetworkConfigureCmdArgs

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent.parent.parent}/rpi/config.yaml"
# CONFIG_INTERNAL_PATH = pkgutil.get_data(__name__, "rpi/config.yaml")

ConfigResolver.resolve(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH)
TyperRemoteOpts.load(ConfigResolver.config)

os_cli_app = typer.Typer()


@os_cli_app.command(name="burn-image", no_args_is_help=True)
@logger.catch(reraise=True)
def burn_image(
    image_download_url: Optional[str] = typer.Option(
        ConfigResolver.get_config().get_os_raspbian_download_url(),
        help="OS image file download URL",
        envvar="IMAGE_DOWNLOAD_URL",
    )
) -> None:
    """
    Select an available block device to burn a Raspbian OS image (SD-Card / HDD)
    """
    try:
        args = RPiOsBurnImageCmdArgs(
            image_download_url=image_download_url, image_download_path=ConfigResolver.get_config().rpi.os.download_path
        )
        args.print()
        RPiOsBurnImageCmd().run(ctx=CliContextManager.create(), args=args)
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
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
    Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
    """
    try:
        args = RPiOsConfigureCmdArgs(
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts),
        )
        args.print()
        RPiOsConfigureCmd().run(ctx=CliContextManager.create(), args=args)
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
        None, show_default=False, help="Static IP address to set as the remote host IP address", envvar="RPI_STATIC_IP"
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
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
    """
    try:
        args = RPiNetworkConfigureCmdArgs(
            gw_ip_address=gw_ip_address,
            dns_ip_address=dns_ip_address,
            static_ip_address=static_ip_address,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts),
        )
        args.print()
        RPiNetworkConfigureCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
