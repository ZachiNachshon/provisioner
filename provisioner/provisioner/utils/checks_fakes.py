#!/usr/bin/env python3

from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.checks import Checks


class FakeChecks(TestFakes, Checks):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        Checks.__init__(self, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakeChecks":
        fake = FakeChecks(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.check_tool_fn = MagicMock(side_effect=fake.check_tool_fn)
        fake.is_tool_exist_fn = MagicMock(side_effect=fake.is_tool_exist_fn)
        return fake

    def is_tool_exist_fn(self, name: str) -> bool:
        return self.trigger_side_effect("is_tool_exist_fn", name)

    def check_tool_fn(self, name: str) -> None:
        return self.trigger_side_effect("check_tool_fn", name)
