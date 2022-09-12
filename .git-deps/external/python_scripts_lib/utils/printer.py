#!/usr/bin/env python3

from loguru import logger

from ..infra.context import Context
from ..colors.color import *

class Printer:

    _dry_run: bool = None
    _verbose: bool = None

    def __init__(self, dry_run: bool, verbose: bool) -> None:
        self._dry_run = dry_run
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context) -> "Printer":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating output printer (dry_run: {dry_run}, verbose: {verbose})...")
        return Printer(dry_run, verbose)

    def _print(self, message: str) -> None:
        if self._dry_run and message:
            message = f"{BOLD}{MAGENTA}[DRY-RUN]{NONE} {message}"
            
        print(message)

    print_fn = _print
