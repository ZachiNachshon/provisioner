#!/usr/bin/env python3

from enum import Enum
from typing import Optional

import click

MODIFIERS_CLICK_CTX_NAME = "cli_modifiers"


# Expose Python interpreter and package manager

class PackageManager(Enum):
    # https://github.com/astral-sh/uv
    PIP = "pip"
    UV = "uv"
    # CONDA = "conda"
    # POETRY = "poetry"
    # PIPENV = "pipenv"
    # ANACONDA = "anaconda"
    # MINICONDA = "miniconda"
    # VIRTUALENV = "virtualenv"
    # VENV = "venv"
    # PIPX = "pipx"

    def __str__(self):
        return self.value

class CliModifiers:

    def __init__(self, verbose: bool, dry_run: bool, auto_prompt: bool, non_interactive: bool, os_arch: str, pkg_mgr: PackageManager) -> None:
        self.verbose = verbose
        self.dry_run = dry_run
        self.auto_prompt = auto_prompt
        self.non_interactive = non_interactive
        self.os_arch = os_arch
        self.pkg_mgr = pkg_mgr

    @staticmethod
    def from_click_ctx(ctx: click.Context) -> Optional["CliModifiers"]:
        """Returns the current singleton instance, if any."""
        return ctx.obj.get(MODIFIERS_CLICK_CTX_NAME, None) if ctx.obj else None

    def is_verbose(self) -> bool:
        return self.verbose

    def is_dry_run(self) -> bool:
        return self.dry_run

    def is_auto_prompt(self) -> bool:
        return self.auto_prompt

    def is_non_interactive(self) -> bool:
        return self.non_interactive

    def maybe_get_os_arch_flag_value(self) -> str:
        return self.os_arch
    
    def get_package_manager(self) -> PackageManager:
        return self.pkg_mgr
