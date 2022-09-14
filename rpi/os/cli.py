#!/usr/bin/env python3

from typing import Optional
from external.python_scripts_lib.utils.os import OsArch
import typer
from loguru import logger
from rpi.os.install import RPiOsInstallArgs, RPiOsInstallCollaborators, RPiOsInstallRunner, RPiOsInstallArgs
from external.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.errors.cli_errors import CliApplicationException

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
    except Exception as e:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        raise CliApplicationException(e)


# @os_cli_app.command(name="configure")
# @logger.catch(reraise=True)
# def configure() -> None:
#     """
#     Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
#     Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
#     """
#     args = OsInstallArgs()
#     args.print()
#     try:
#         ctx = Context.create(verbose=CliGlobalArgs.is_verbose(), dry_run=CliGlobalArgs.is_dry_run())
#         # runner = MachineInfoRunner()
#         # runner.run(ctx=ctx, args=args, collaborators=MachineInfoCollaborators())
#         logger.info("hello configure")
#     except Exception as e:
#         logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
#         raise CliApplicationException(e)
