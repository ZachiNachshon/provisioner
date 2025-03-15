#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable

import click
from loguru import logger

from provisioner_shared.components.runtime.cli.menu_format import GroupedOption, normalize_cli_item
from provisioner_shared.components.runtime.cli.modifiers import MODIFIERS_CLICK_CTX_NAME, CliModifiers, PackageManager
from provisioner_shared.components.runtime.infra.log import LoggerManager

MODIFIERS_GROUP_NAME = "Modifiers"

MODIFIERS_OPT_VERBOSE = "verbose"
MODIFIERS_OPT_AUTO_PROMPT = "auto-prompt"
MODIFIERS_OPT_DRY_RUN = "dry-run"
MODIFIERS_OPT_NON_INTERACTIVE = "non-interactive"
MODIFIERS_OPT_OS_ARCH = "os-arch"
MODIFIERS_OPT_PKG_MGR = "package-manager"


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
    @click.option(
        f"--{MODIFIERS_OPT_PKG_MGR}",
        default=PackageManager.PIP.value,
        show_default=True,
        type=click.Choice([v.value for v in PackageManager], case_sensitive=False),
        envvar="PROV_MODIFIERS_PKG_MGR",
        help=f"Specify a Python package manager  [default: {PackageManager.PIP.value}]",
        cls=GroupedOption,
        group=MODIFIERS_GROUP_NAME,
    )
    @wraps(func)
    @click.pass_context  # Decorator to pass context to the function
    def wrapper(ctx, *args: Any, **kwargs: Any) -> Any:
        verbose = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_VERBOSE), False)
        dry_run = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_DRY_RUN), False)
        auto_prompt = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_AUTO_PROMPT), False)
        non_interactive = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_NON_INTERACTIVE), False)
        os_arch = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_OS_ARCH), None)
        pkg_mgr = kwargs.pop(normalize_cli_item(MODIFIERS_OPT_PKG_MGR), None)

        # Add a state tracker to the context object
        if ctx.obj is None:
            ctx.obj = {}

        if MODIFIERS_CLICK_CTX_NAME not in ctx.obj:
            # First-time initialization
            ctx.obj[MODIFIERS_CLICK_CTX_NAME] = CliModifiers(
                verbose=verbose,
                dry_run=dry_run,
                auto_prompt=auto_prompt,
                non_interactive=non_interactive,
                os_arch=os_arch,
                pkg_mgr=PackageManager.from_str(pkg_mgr),
            )
            logger.debug("Initialized CliModifiers for the first time.")
        else:
            # Update only the relevant fields if they change
            modifiers = ctx.obj[MODIFIERS_CLICK_CTX_NAME]

            if verbose and not modifiers.verbose:
                modifiers.verbose = True
                click.echo("Verbose output: enabled")

            if dry_run and not modifiers.dry_run:
                modifiers.dry_run = True
                click.echo("Dry run: enabled")

            if auto_prompt and not modifiers.auto_prompt:
                modifiers.auto_prompt = True
                click.echo("Auto prompt: enabled")

            if non_interactive and not modifiers.non_interactive:
                modifiers.non_interactive = True
                click.echo("Non interactive: enabled")

            if os_arch and modifiers.os_arch != os_arch:
                modifiers.os_arch = os_arch
                click.echo(f"OS_Arch updated to: {os_arch}")

            if (
                pkg_mgr
                and modifiers.pkg_mgr
                and modifiers.pkg_mgr.value.lower() != PackageManager.from_str(pkg_mgr).value.lower()
            ):
                modifiers.pkg_mgr = PackageManager.from_str(pkg_mgr)
                click.echo(f"Package manager: {pkg_mgr}")

        # Access the current state
        modifiers = ctx.obj[MODIFIERS_CLICK_CTX_NAME]

        # Logger Manager Initialization (only once)
        if "_logger_initialized" not in ctx.obj:
            logger_mgr = LoggerManager()
            logger_mgr.initialize(modifiers.verbose, modifiers.dry_run)
            ctx.obj["_logger_initialized"] = True  # Ensure it's only done once

        return func(*args, **kwargs)

    return wrapper
