#!/usr/bin/env python3

import typer
from typing import Optional
from loguru import logger
from rpi.os.install import RPiOsInstallArgs, RPiOsInstallCollaborators, RPiOsInstallRunner, RPiOsInstallArgs
from rpi.os.configure import RPiOsConfigureArgs, RPiOsConfigureCollaborators, RPiOsConfigureRunner, RPiOsConfigureArgs
from rpi.os.network import (
    RPiNetworkConfigureArgs,
    RPiNetworkConfigureCollaborators,
    RPiNetworkConfigureRunner,
    RPiNetworkConfigureArgs,
)
from external.python_scripts_lib.python_scripts_lib.utils.os import OsArch
from external.python_scripts_lib.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)

os_cli_app = typer.Typer()


@os_cli_app.command(name="install")
@logger.catch(reraise=True)
def install(
    image_download_url: Optional[str] = typer.Option(
        None, help="OS image file download URL", envvar="IMAGE_DOWNLOAD_URL"
    )
) -> None:
    """
    Select an available SD-CARD to burn a Raspbian OS image
    """
    args = RPiOsInstallArgs(image_download_url=image_download_url)
    args.print()
    try:
        os_arch_str = CliGlobalArgs.maybe_get_os_arch_flag_value()
        os_arch = OsArch.from_string(os_arch_str) if os_arch_str else None

        ctx = Context.create(
            dry_run=CliGlobalArgs.is_dry_run(),
            verbose=CliGlobalArgs.is_verbose(),
            auto_prompt=CliGlobalArgs.is_auto_prompt(),
            os_arch=os_arch,
        )

        RPiOsInstallRunner().run(ctx=ctx, args=args, collaborators=RPiOsInstallCollaborators(ctx))
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


@os_cli_app.command(name="configure")
@logger.catch(reraise=True)
def configure(
    node_username: Optional[str] = typer.Option(None, help="RPi node username", envvar="NODE_USERNAME"),
    node_password: Optional[str] = typer.Option(None, help="RPi node password", envvar="NODE_PASSWORD"),
    ip_discovery_range: Optional[str] = typer.Option(
        None, help="LAN network IP discovery range", envvar="IP_DISCOVERY_RANGE"
    ),
) -> None:
    """
    Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
    Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
    """
    args = RPiOsConfigureArgs(
        node_username=node_username, node_password=node_password, ip_discovery_range=ip_discovery_range
    )
    args.print()
    try:
        os_arch_str = CliGlobalArgs.maybe_get_os_arch_flag_value()
        os_arch = OsArch.from_string(os_arch_str) if os_arch_str else None

        ctx = Context.create(
            dry_run=CliGlobalArgs.is_dry_run(),
            verbose=CliGlobalArgs.is_verbose(),
            auto_prompt=CliGlobalArgs.is_auto_prompt(),
            os_arch=os_arch,
        )

        RPiOsConfigureRunner().run(ctx=ctx, args=args, collaborators=RPiOsConfigureCollaborators(ctx))
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


@os_cli_app.command(name="network")
@logger.catch(reraise=True)
def configure(
    node_username: Optional[str] = typer.Option(None, help="RPi node username", envvar="NODE_USERNAME"),
    node_password: Optional[str] = typer.Option(None, help="RPi node password", envvar="NODE_PASSWORD"),
    ip_discovery_range: Optional[str] = typer.Option(
        None, help="LAN network IP discovery range", envvar="IP_DISCOVERY_RANGE"
    ),
    gw_ip_address: Optional[str] = typer.Option(
        None, help="Internet gateway address / home router address", envvar="GATEWAY_ADDRESS"
    ),
    dns_ip_address: Optional[str] = typer.Option(
        None, help="Domain name server address / home router address", envvar="DNS_ADDRESS"
    ),
    static_ip_address: Optional[str] = typer.Option(
        None, help="Static IP address to set as the remote host IP address", envvar="RPI_STATIC_IP"
    ),
) -> None:
    """
    Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
    """
    args = RPiNetworkConfigureArgs(
        node_username=node_username,
        node_password=node_password,
        ip_discovery_range=ip_discovery_range,
        gw_ip_address=gw_ip_address,
        dns_ip_address=dns_ip_address,
        static_ip_address=static_ip_address,
    )
    args.print()
    try:
        os_arch_str = CliGlobalArgs.maybe_get_os_arch_flag_value()
        os_arch = OsArch.from_string(os_arch_str) if os_arch_str else None

        ctx = Context.create(
            dry_run=CliGlobalArgs.is_dry_run(),
            verbose=CliGlobalArgs.is_verbose(),
            auto_prompt=CliGlobalArgs.is_auto_prompt(),
            os_arch=os_arch,
        )

        RPiNetworkConfigureRunner().run(ctx=ctx, args=args, collaborators=RPiNetworkConfigureCollaborators(ctx))
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
