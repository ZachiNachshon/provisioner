#!/usr/bin/env python3

from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.progress_indicator import ProgressIndicator


class FakePrinter(Printer):

    registered_output: List[str] = None

    def __init__(self, progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool):
        super().__init__(progress_indicator=progress_indicator, dry_run=dry_run, verbose=verbose)
        self.registered_output = []

    @staticmethod
    def _create_fake(progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool) -> "FakePrinter":
        printer = FakePrinter(progress_indicator=progress_indicator, dry_run=dry_run, verbose=verbose)
        printer.print_fn = lambda message: printer._register_message(message)
        printer.new_line_fn = lambda count=1: printer
        printer.print_horizontal_line_fn = lambda message, line_color="green": printer._register_message(message)
        printer.print_with_rich_table_fn = lambda message, border_color="green": printer._register_message(message)
        return printer

    @staticmethod
    def create(ctx: Context, progress_indicator: ProgressIndicator) -> "FakePrinter":
        return FakePrinter._create_fake(
            progress_indicator=progress_indicator, dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose()
        )

    def _register_message(self, message: str) -> "FakePrinter":
        self.registered_output.append(message)
        return self

    def assert_output(self, message: str) -> None:
        found = False
        for output in self.registered_output:
            if message in output:
                found = True
                break
        if not found:
            raise FakeEnvironmentAssertionError(
                f"Printer expected an output message but it never printed. message:\n{message}"
            )

    def assert_outputs(self, messages: List[str]) -> None:
        for message in messages:
            self.assert_output(message)
