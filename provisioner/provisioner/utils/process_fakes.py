#!/usr/bin/env python3

from typing import List, Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.process import Process


class FakeProcess(TestFakes, Process):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        Process.__init__(self, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakeProcess":
        fake = FakeProcess(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.run_fn = MagicMock(side_effect=fake.run_fn)
        fake.is_tool_exist_fn = MagicMock(side_effect=fake.is_tool_exist_fn)
        return fake

    def run_fn(
        self,
        args: List[str],
        working_dir: Optional[str] = None,
        fail_msg: Optional[str] = "",
        fail_on_error: Optional[bool] = True,
        allow_single_shell_command_str: Optional[bool] = False,
    ) -> bool:
        return self.trigger_side_effect(
            "run_fn", args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str
        )

    def is_tool_exist_fn(self, name: str) -> bool:
        return self.trigger_side_effect("is_tool_exist_fn", name)
