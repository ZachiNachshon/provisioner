#!/usr/bin/env python3

from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.package_loader import PackageLoader


class FakePackageLoader(TestFakes, PackageLoader):
    def __init__(self, ctx: Context):
        TestFakes.__init__(self)
        PackageLoader.__init__(self, ctx)

    @staticmethod
    def create(ctx: Context) -> "FakePackageLoader":
        fake = FakePackageLoader(ctx)
        fake.check_tool_fn = MagicMock(side_effect=fake.check_tool_fn)
        fake.is_tool_exist_fn = MagicMock(side_effect=fake.is_tool_exist_fn)
        return fake

    def is_tool_exist_fn(self, name: str) -> bool:
        return self.trigger_side_effect("is_tool_exist_fn", name)

    def check_tool_fn(self, name: str) -> None:
        return self.trigger_side_effect("check_tool_fn", name)
