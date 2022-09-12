#!/usr/bin/env python3

from ..infra.context import Context
from .printer import Printer

class FakePrinter(Printer):

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakePrinter":
        process = FakePrinter(dry_run=dry_run, verbose=verbose)
        process.print_fn = lambda message: None
        return process

    @staticmethod
    def create(ctx: Context) -> "FakePrinter":
        return FakePrinter._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        