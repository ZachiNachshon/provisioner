#!/usr/bin/env python3

from typing import Optional

from loguru import logger
from rich.console import Console
from rich.table import Table

from provisioner.colors import colors
from provisioner.colors.colors import *
from provisioner.infra.context import Context

FIXED_CONSOLE_WIDTH = 100


class Printer:

    _dry_run: bool = None
    _verbose: bool = None
    console = None

    def __init__(self, dry_run: bool, verbose: bool) -> None:
        self._dry_run = dry_run
        self._verbose = verbose
        self.console = Console(width=FIXED_CONSOLE_WIDTH)

    @staticmethod
    def create(ctx: Context) -> "Printer":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating output printer (dry_run: {dry_run}, verbose: {verbose})...")
        return Printer(dry_run, verbose)

    def _print(self, message: str) -> "Printer":
        if self._dry_run and message:
            message = f"{colors.BOLD}{colors.MAGENTA}[DRY-RUN]{colors.NONE} {message}"

        print(message)
        return self

    def _print_with_rich_table(self, message: str, border_color: Optional[str] = "green") -> "Printer":
        """
        Message text supports Python rich format i.e. [green]Hello[/green]
        List of colors can be found on the following link:
          https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors
        """
        if self._dry_run and message:
            message = f"[bold magenta][DRY-RUN][/bold magenta] {message}"

        table = Table(
            show_edge=True,
            show_header=False,
            caption_justify="left",
            border_style=border_color,
            width=FIXED_CONSOLE_WIDTH,
        )
        table.add_column(no_wrap=True, justify="left")
        table.add_row(message, end_section=True)
        self.console.print()
        self.console.print(table, justify="left")
        self.console.print()
        return self

    def _print_horizontal_line(self, message: str, line_color: Optional[str] = "green") -> None:
        self.console.rule(f"[bold {line_color}]{message}", align="center")

    def _new_line(self, count: Optional[int] = 1) -> "Printer":
        for i in range(count):
            self.console.print()
        return self

    print_fn = _print
    print_with_rich_table_fn = _print_with_rich_table
    print_horizontal_line_fn = _print_horizontal_line
    new_line_fn = _new_line
