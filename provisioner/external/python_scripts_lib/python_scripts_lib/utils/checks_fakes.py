#!/usr/bin/env python3

from typing import Any, Optional

from ..errors.cli_errors import MissingUtilityException
from ..infra.context import Context
from .checks import Checks


class FakeChecks(Checks):

    registered_utilities: dict[str, bool] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.registered_utilities = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeChecks":
        checks = FakeChecks(dry_run=dry_run, verbose=verbose)
        checks.is_tool_exist_fn = lambda name: checks._utilities_selector(name, soft_fail=True)
        checks.check_tool_fn = lambda name: checks._utilities_selector(name, soft_fail=False)
        return checks

    @staticmethod
    def create(ctx: Context) -> "FakeChecks":
        return FakeChecks._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def register_utility(self, name: str, exist: Optional[bool] = True):
        self.registered_utilities[name] = exist

    def _utilities_selector(self, name: str, soft_fail: bool) -> Any:
        for key in self.registered_utilities.keys():
            # If utility was registered and marked as exists
            if name == key and self.registered_utilities[key]:
                return self.registered_utilities[key]

        if soft_fail:
            return False

        raise MissingUtilityException(f"Fake checked utility is not defined. name: {name}")
