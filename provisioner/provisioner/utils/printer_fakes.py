#!/usr/bin/env python3

from typing import Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.printer import Printer


class FakePrinter(TestFakes, Printer):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        Printer.__init__(self, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakePrinter":
        fake = FakePrinter(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.print_fn = MagicMock(side_effect=fake.print_fn)
        fake.print_with_rich_table_fn = MagicMock(side_effect=fake.print_with_rich_table_fn)
        fake.print_horizontal_line_fn = MagicMock(side_effect=fake.print_horizontal_line_fn)
        fake.new_line_fn = MagicMock(side_effect=fake.new_line_fn)
        return fake

    def print_fn(self, message: str) -> "Printer":
        return self.trigger_side_effect("print_fn", message)

    def print_with_rich_table_fn(self, message: str, border_color: Optional[str] = "green") -> "Printer":
        return self.trigger_side_effect("print_with_rich_table_fn", message, border_color)

    def print_horizontal_line_fn(self, message: str, line_color: Optional[str] = "green") -> None:
        return self.trigger_side_effect("print_horizontal_line_fn", message, line_color)

    def new_line_fn(self, count: Optional[int] = 1) -> "Printer":
        return self.trigger_side_effect("new_line_fn", count)
