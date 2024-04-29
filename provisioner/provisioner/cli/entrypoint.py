#!/usr/bin/env python3

from typing import Callable, Optional

import typer
from loguru import logger

from provisioner.cli.state import CliGlobalArgs
from provisioner.infra.context import Context
from provisioner.infra.log import LoggerManager
from provisioner.utils.paths import Paths

STATIC_RESOURCES_PACKAGE = "provisioner.resources"

MODIFIERS_FLAGS_GROUP_NAME = "Modifiers"

def main_runner(
    verbose: Optional[bool] = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Run command with DEBUG verbosity",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME,
    ),
    auto_prompt: Optional[bool] = typer.Option(
        False,
        "--auto-prompt",
        "-y",
        help="Do not prompt for approval and accept everything",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME,
    ),
    dry_run: Optional[bool] = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Run command as NO-OP, print commands to output, do not execute",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME,
    ),
    non_interactive: Optional[bool] = typer.Option(
        False,
        "--non-interactive",
        "-n",
        help="Turn off interactive prompts and outputs, basic output only",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME,
    ),
    os_arch: Optional[str] = typer.Option(
        None,
        "--os-arch",
        help="Specify a OS_ARCH tuple manually",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME,
    ),
    version: Optional[bool] = typer.Option(
        False, "--version", help="Print client version", is_flag=True, rich_help_panel=MODIFIERS_FLAGS_GROUP_NAME
    ),
) -> None:

    if version:
        print(try_read_version())
        typer.Exit(0)

    if verbose:
        typer.echo("Verbose output: enabled")

    if dry_run:
        typer.echo("Dry run: enabled")

    if auto_prompt:
        typer.echo("Auto prompt: enabled")

    if non_interactive:
        typer.echo("Non interactive: enabled")

    if os_arch:
        typer.echo(f"OS_Arch supplied manually: {os_arch}")

    # if not state_was_initialized():
    CliGlobalArgs.create(verbose, dry_run, auto_prompt, non_interactive, os_arch)
    logger_mgr = LoggerManager()
    logger_mgr.initialize(verbose, dry_run)


def try_read_version() -> str:
    content = "no version"
    try:
        file_path = Paths.create(Context.create()).get_file_path_from_python_package(
            STATIC_RESOURCES_PACKAGE, "version.txt"
        )
        with open(file_path, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception as ex:
        logger.error(f"Failed to read version file. ex: {ex}")
        pass
    return content


class EntryPoint:
    @staticmethod
    def create_typer(
        title: str,
        config_resolver_fn: Optional[Callable] = None,
        version_package_path: Optional[str] = STATIC_RESOURCES_PACKAGE,
    ) -> typer.Typer:

        if len(version_package_path) > 0:
            global STATIC_RESOURCES_PACKAGE
            STATIC_RESOURCES_PACKAGE = version_package_path

        if config_resolver_fn:
            config_resolver_fn()

        # Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
        # Use also no_args_is_help=True to print the help menu if no arguments were supplied
        return typer.Typer(
            help=title, callback=main_runner, invoke_without_command=True, no_args_is_help=True, rich_markup_mode=None
        )
