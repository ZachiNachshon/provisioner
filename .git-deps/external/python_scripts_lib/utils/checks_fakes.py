#!/usr/bin/env python3

from .checks import Checks
from ..errors.cli_errors import MissingUtilityException

class FakeChecks(Checks):

    registered_utilities: dict[str, bool] = {}

    def __init__(self):
        super().__init__()
        self.registered_utilities = {}

    @staticmethod
    def _create_fake() -> "FakeChecks":
        checks = FakeChecks()
        checks.is_tool_exist_fn = lambda name: name
        checks.check_tool_fn = lambda name: checks._utilities_selector(name)
        return checks

    @staticmethod
    def create() -> "FakeChecks":
        return FakeChecks._create_fake()

    def register_utility(self, name: str):
        self.registered_utilities[name] = True

    def _utilities_selector(self, name: str) -> str:
        print(f"registered_utilities: {self.registered_utilities}")
        if name not in self.registered_utilities:
            raise MissingUtilityException(f"Fake checked utility is not defined. name: {name}")
