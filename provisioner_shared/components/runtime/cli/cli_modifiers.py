#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable

import click
from components.runtime.cli.menu_format import GroupedOption

from provisioner_shared.components.runtime.cli.state import CliGlobalArgs
from provisioner_shared.components.runtime.infra.log import LoggerManager

# Define modifiers globally
def cli_modifiers(func: Callable) -> Callable:
    @click.option(
        "--verbose", "-v",
        is_flag=True,
        help="Run command with DEBUG verbosity",
        cls=GroupedOption, 
        group="Modifiers"
    )
    @click.option(
        "--auto-prompt", "-y",
        is_flag=True,
        help="Do not prompt for approval and accept everything",
        cls=GroupedOption, 
        group="Modifiers"
    )
    @click.option(
        "--dry-run", "-d",
        is_flag=True,
        help="Run command as NO-OP, print commands to output, do not execute",
        cls=GroupedOption, 
        group="Modifiers"
    )
    @click.option(
        "--non-interactive", "-n",
        is_flag=True,
        help="Turn off interactive prompts and outputs, basic output only",
        cls=GroupedOption, 
        group="Modifiers"
    )
    @click.option(
        "--os-arch",
        type=str,
        help="Specify a OS_ARCH tuple manually",
        cls=GroupedOption, 
        group="Modifiers"
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verbose = kwargs.pop('verbose', False)
        if verbose:
            click.echo("Verbose output: enabled")

        dry_run = kwargs.pop('dry_run', False)
        if dry_run:
            click.echo("Dry run: enabled")

        auto_prompt = kwargs.pop('auto_prompt', False)
        if auto_prompt:
            click.echo("Auto prompt: enabled")

        non_interactive = kwargs.pop('non_interactive', False)
        if non_interactive:
            click.echo("Non interactive: enabled")

        os_arch = kwargs.pop('os_arch', None)
        if os_arch:
            click.echo(f"OS_Arch supplied manually: {os_arch}")

        CliGlobalArgs.create(verbose, dry_run, auto_prompt, non_interactive, os_arch)
        logger_mgr = LoggerManager()
        logger_mgr.initialize(verbose, dry_run)
        return func(*args, **kwargs)
    return wrapper

