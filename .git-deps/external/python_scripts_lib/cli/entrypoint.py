#!/usr/bin/env python3

import typer
from typing import Optional
from external.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.infra.log import LoggerManager


def main_runner(
    verbose: Optional[bool] = typer.Option(False, "--verbose", "-v", help="Run command with DEBUG verbosity"),
    auto_prompt: Optional[bool] = typer.Option(
        False, "--auto-prompt", "-y", help="Do not prompt for approval and accept everything"
    ),
    dry_run: Optional[bool] = typer.Option(
        False, "--dry-run", "-d", help="Run command as NO-OP, print commands to output, do not execute"
    ),
) -> None:
    """
    General purpose utilities
    """
    if verbose:
        typer.echo("Verbose output: enabled")

    if dry_run:
        typer.echo("Dry run: enabled")

    if auto_prompt:
        typer.echo("Auto prompt: enabled")

    CliGlobalArgs.create(verbose, dry_run, auto_prompt)
    logger_mgr = LoggerManager()
    logger_mgr.initialize(verbose, dry_run)
