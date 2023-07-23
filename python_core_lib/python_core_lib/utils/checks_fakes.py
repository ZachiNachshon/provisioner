#!/usr/bin/env python3

from typing import Optional

from python_core_lib.errors.cli_errors import MissingUtilityException
from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.checks import Checks


class FakeChecks(Checks):

    __registered_is_tool_exists: dict[str, bool] = None
    __registered_check_tool: dict[str, bool] = None

    __mocked_utilities_install_status: dict[str, bool] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(dry_run=dry_run, verbose=verbose)
        self.__registered_is_tool_exists = {}
        self.__registered_check_tool = {}
        self.__mocked_utilities_install_status = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeChecks":
        checks = FakeChecks(dry_run=dry_run, verbose=verbose)
        checks.is_tool_exist_fn = lambda name: checks._register_is_tool_exist(name)
        checks.check_tool_fn = lambda name: checks._register_check_tool(name)
        return checks

    @staticmethod
    def create(ctx: Context) -> "FakeChecks":
        return FakeChecks._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def _register_is_tool_exist(self, name: str) -> bool:
        status = self.__mocked_utilities_install_status.get(name, False)
        self.__registered_is_tool_exists[name] = status
        return status

    def assert_is_tool_exist(self, name: str, exist: bool) -> None:
        if name not in self.__registered_is_tool_exists:
            raise FakeEnvironmentAssertionError(
                f"Checks expected a check if tool exists but it never triggered. name: {name}"
            )
        elif exist != self.__registered_is_tool_exists[name]:
            raise FakeEnvironmentAssertionError(
                "Checks expected a check if tool exists but the result differ.\n"
                + f"Actual:\n{self.__registered_is_tool_exists[name]}\n"
                + f"Expected:\n{exist}"
            )

    def _register_check_tool(self, name: str) -> bool:
        status = self.__mocked_utilities_install_status.get(name, False)
        if not status:
            # To allow the same flow as with the real Checks utilitie, we must raise an error
            # in case the check_tool function fails
            raise MissingUtilityException(f"missing CLI tool. name: {name}")
        self.__registered_check_tool[name] = status
        return status

    def assert_check_tool(self, name: str, status: bool) -> None:
        if name not in self.__registered_check_tool:
            raise FakeEnvironmentAssertionError(
                f"Checks expected a check for a tool status but it never triggered. name: {name}"
            )
        elif status != self.__registered_check_tool[name]:
            raise FakeEnvironmentAssertionError(
                "Checks expected a check for a tool status but the result differ.\n"
                + f"Actual:\n{self.__registered_check_tool[name]}\n"
                + f"Expected:\n{status}"
            )

    def mock_utility(self, name: str, exist: Optional[bool] = True) -> "FakeChecks":
        self.__mocked_utilities_install_status[name] = exist
        return self
