#!/usr/bin/env python3

from typing import Optional

from loguru import logger
from rich.console import Console
from rich.table import Table

from ..colors import color
from ..colors.color import *
from ..infra.context import Context
from .progress_indicator import ProgressIndicator

FIXED_CONSOLE_WIDTH=100

class Printer:

    _dry_run: bool = None
    _verbose: bool = None
    progress_indicator = None
    console = None

    def __init__(self, progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool) -> None:
        self.progress_indicator = progress_indicator
        self._dry_run = dry_run
        self._verbose = verbose
        self.console = Console(width=FIXED_CONSOLE_WIDTH)

    @staticmethod
    def create(ctx: Context, progress_indicator: ProgressIndicator) -> "Printer":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating output printer (dry_run: {dry_run}, verbose: {verbose})...")
        return Printer(progress_indicator, dry_run, verbose)

    def _print(self, message: str) -> None:
        if self._dry_run and message:
            message = f"{color.BOLD}{color.MAGENTA}[DRY-RUN]{color.NONE} {message}"

        print(message)

    def _print_with_rich_table(self, message: str, border_color: Optional[str] = "green") -> None:
        """
        Text support Python rich format i.e. [green]Hello[/green]
        List of colors can be found on the following link:
          https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors
        """
        if self._dry_run and message:
            message = f"[bold magenta][DRY-RUN][/bold magenta] {message}"

        table = Table(show_edge=True, show_header=False, caption_justify="left", border_style=border_color, width=FIXED_CONSOLE_WIDTH)
        table.add_column(no_wrap=True, justify="left")
        table.add_row(message, end_section=True)
        self.console.print()
        self.console.print(table, justify="left")
        self.console.print()

    def _print_horizontal_line(self, message: str, line_color: Optional[str] = "green") -> None:
        self.console.rule(f"[bold {line_color}]{message}", align="center")

    def _new_line(self, count: Optional[int] = 1) -> None:
        for i in range(count):
            self.console.print()

    print_fn = _print
    print_with_rich_table_fn = _print_with_rich_table
    print_horizontal_line_fn = _print_horizontal_line
    new_line_fn = _new_line
