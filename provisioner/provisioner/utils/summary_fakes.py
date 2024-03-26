#!/usr/bin/env python3

from typing import Any, Callable
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.json_util import JsonUtil
from provisioner.utils.summary import Summary


class FakeSummary(TestFakes, Summary):
    def __init__(self, json_util: JsonUtil):
        TestFakes.__init__(self)
        Summary.__init__(
            self, dry_run=True, verbose=False, auto_prompt=False, json_util=json_util, printer=None, prompter=None
        )

    @staticmethod
    def create(ctx: Context) -> "FakeSummary":
        fake = FakeSummary(JsonUtil.create(ctx=ctx, io_utils=None))
        fake.append = MagicMock(side_effect=fake.append)
        fake.append_result = MagicMock(side_effect=fake.append_result)
        fake.show_summary_and_prompt_for_enter = MagicMock(side_effect=fake.show_summary_and_prompt_for_enter)
        return fake

    def append(self, attribute_name: str, value: Any) -> bool:
        return self.trigger_side_effect("append", attribute_name, value)

    def append_result(self, attribute_name: str, call: Callable[[], str]) -> bool:
        return self.trigger_side_effect("append_result", attribute_name, call)

    def show_summary_and_prompt_for_enter(self, title: str) -> None:
        return self.trigger_side_effect("show_summary_and_prompt_for_enter", title)
