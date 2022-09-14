#!/usr/bin/env python3

from .checks import Checks
from ..errors.cli_errors import MissingUtilityException
from ..infra.context import Context

class FakeChecks(Checks):

    registered_utilities: dict[str, bool] = {}

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.registered_utilities = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeChecks":
        checks = FakeChecks(dry_run=dry_run, verbose=verbose)
        checks.is_tool_exist_fn = lambda name: name
        checks.check_tool_fn = lambda name: checks._utilities_selector(name)
        return checks

    @staticmethod
    def create(ctx: Context) -> "FakeChecks":
        return FakeChecks._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def register_utility(self, name: str):
        self.registered_utilities[name] = True

    def _utilities_selector(self, name: str) -> str:
        print(f"registered_utilities: {self.registered_utilities}")
        if name not in self.registered_utilities:
            raise MissingUtilityException(f"Fake checked utility is not defined. name: {name}")
