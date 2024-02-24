#!/usr/bin/env python3

from typing import Optional


class RemoteContext:
    _verbose: bool = None
    _dry_run: bool = None
    _silent: bool = None

    @staticmethod
    def no_op() -> "RemoteContext":
        return RemoteContext()

    @staticmethod
    def create(
        dry_run: Optional[bool] = False,
        verbose: Optional[bool] = False,
        silent: Optional[bool] = False,
    ) -> "RemoteContext":

        ctx = RemoteContext()
        ctx._dry_run = dry_run
        ctx._verbose = verbose
        ctx._silent = silent
        return ctx

    def is_verbose(self) -> bool:
        return self._verbose

    def is_dry_run(self) -> bool:
        return self._dry_run

    def is_silent(self) -> bool:
        return self._silent
