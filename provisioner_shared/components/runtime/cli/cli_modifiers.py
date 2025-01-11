#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable

import click

from components.runtime.cli.menu_format import GroupedOption, normalize_cli_item
from provisioner_shared.components.runtime.cli.state import CliGlobalArgs
from provisioner_shared.components.runtime.infra.log import LoggerManager

MODIFIERS_GROUP_NAME = "Modifiers"

MODIFIERS_OPT_VERBOSE = "verbose"
MODIFIERS_OPT_AUTO_PROMPT = "auto-prompt"
MODIFIERS_OPT_DRY_RUN = "dry-run"
MODIFIERS_OPT_NON_INTERACTIVE = "non-interactive"
MODIFIERS_OPT_OS_ARCH = "os-arch"


# Define modifiers globally
def cli_modifiers(func: Callable) -> Callable:
    @click.option(
        f"--{MODIFIERS_OPT_VERBOSE}",
        "-v",
        is_flag=True,
        help="Run command with DEBUG verbosity",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @click.option(
        f"--{MODIFIERS_OPT_AUTO_PROMPT}",
        "-y",
        is_flag=True,
        help="Do not prompt for approval and accept everything",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @click.option(
        f"--{MODIFIERS_OPT_DRY_RUN}",
        "-d",
        is_flag=True,
        help="Run command as NO-OP, print commands to output, do not execute",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @click.option(
        f"--{MODIFIERS_OPT_NON_INTERACTIVE}",
        "-n",
        is_flag=True,
        help="Turn off interactive prompts and outputs, basic output only",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @click.option(
        f"--{MODIFIERS_OPT_OS_ARCH}",
        type=str,
        help="Specify a OS_ARCH tuple manually",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verbose = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_VERBOSE), False)
        if verbose:
            click.echo("Verbose output: enabled")

        dry_run = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_DRY_RUN), False)
        if dry_run:
            click.echo("Dry run: enabled")

        auto_prompt = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_AUTO_PROMPT), False)
        if auto_prompt:
            click.echo("Auto prompt: enabled")

        non_interactive = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_NON_INTERACTIVE), False)
        if non_interactive:
            click.echo("Non interactive: enabled")

        os_arch = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_OS_ARCH), None)
        if os_arch:
            click.echo(f"OS_Arch supplied manually: {os_arch}")

        CliGlobalArgs.create(verbose, dry_run, auto_prompt, non_interactive, os_arch)
        logger_mgr = LoggerManager()
        logger_mgr.initialize(verbose, dry_run)
        return func(*args, **kwargs)

    return wrapper
