#!/usr/bin/env python3

from typing import Optional

import click

MODIFIERS_CLICK_CTX_NAME = "cli_modifiers"


class CliModifiers:

    def __init__(self, verbose: bool, dry_run: bool, auto_prompt: bool, non_interactive: bool, os_arch: str) -> None:
        self.verbose = verbose
        self.dry_run = dry_run
        self.auto_prompt = auto_prompt
        self.non_interactive = non_interactive
        self.os_arch = os_arch

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
