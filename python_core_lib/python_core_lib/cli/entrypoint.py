#!/usr/bin/env python3

from typing import Callable, Optional

import typer

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.infra.context import Context
from python_core_lib.infra.log import LoggerManager
from python_core_lib.utils.paths import Paths

STATIC_VERSION_PACKAGE_PATH = None

MODIFIERS_FLAGS_HELP_TITLE = "Modifiers"


def main_runner(
    verbose: Optional[bool] = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Run command with DEBUG verbosity",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_HELP_TITLE,
    ),
    auto_prompt: Optional[bool] = typer.Option(
        False,
        "--auto-prompt",
        "-y",
        help="Do not prompt for approval and accept everything",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_HELP_TITLE,
    ),
    dry_run: Optional[bool] = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Run command as NO-OP, print commands to output, do not execute",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_HELP_TITLE,
    ),
    os_arch: Optional[str] = typer.Option(
        None,
        "--os-arch",
        help="Specify a OS_ARCH tuple manually",
        is_flag=True,
        rich_help_panel=MODIFIERS_FLAGS_HELP_TITLE,
    ),
    version: Optional[bool] = typer.Option(
        False, "--version", help="Print client version", is_flag=True, rich_help_panel=MODIFIERS_FLAGS_HELP_TITLE
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

    if os_arch:
        typer.echo(f"OS_Arch supplied manually: {os_arch}")

    # if not state_was_initialized():
    CliGlobalArgs.create(verbose, dry_run, auto_prompt, os_arch)
    logger_mgr = LoggerManager()
    logger_mgr.initialize(verbose, dry_run)


def try_read_version() -> str:
    content = "no version"
    try:
        file_path = Paths.create(Context.create()).get_file_path_from_python_package(
            STATIC_VERSION_PACKAGE_PATH, "version.txt"
        )
        with open(file_path, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception:
        pass
    return content


class EntryPoint:
    @staticmethod
    def create_typer(
        title: str,
        config_resolver_fn: Optional[Callable] = None,
        version_package_path: Optional[str] = "resources",
    ) -> typer.Typer:

        global STATIC_VERSION_PACKAGE_PATH
        STATIC_VERSION_PACKAGE_PATH = version_package_path

        if config_resolver_fn:
            config_resolver_fn()

        # Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
        # Use also no_args_is_help=True to print the help menu if no arguments were supplied
        return typer.Typer(
            help=title, callback=main_runner, invoke_without_command=True, no_args_is_help=True, rich_markup_mode=None
        )
