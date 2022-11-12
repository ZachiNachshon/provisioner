#!/usr/bin/env python3

from ..infra.context import Context
from .printer import Printer
from .progress_indicator import ProgressIndicator
from .progress_indicator_fakes import FakeProgressIndicator


class FakePrinter(Printer):
    def __init__(self, progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool):
        super().__init__(progress_indicator=progress_indicator, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def _create_fake(progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool) -> "FakePrinter":
        printer = FakePrinter(progress_indicator=progress_indicator, dry_run=dry_run, verbose=verbose)
        printer.print_fn = lambda message: None
        printer.new_line_fn = lambda count=1: None
        printer.print_horizontal_line_fn = lambda message, line_color: None
        printer.print_with_rich_table_fn = lambda message, border_color: None
        return printer

    @staticmethod
    def create(ctx: Context) -> "FakePrinter":
        return FakePrinter._create_fake(
            progress_indicator=FakeProgressIndicator.create(ctx), dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose()
        )
