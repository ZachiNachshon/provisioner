#!/usr/bin/env python3

from unittest.mock import MagicMock

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.pypi_registry import PyPiRegistry
from provisioner_shared.test_lib.faker import TestFakes


class FakePyPiRegistry(TestFakes, PyPiRegistry):
    def __init__(self, ctx: Context):
        TestFakes.__init__(self)
        PyPiRegistry.__init__(self, http_client=None)

    @staticmethod
    def create(ctx: Context) -> "FakePyPiRegistry":
        fake = FakePyPiRegistry(ctx)
        fake._get_package_version_fn = MagicMock(side_effect=fake._get_package_version_fn)
        return fake

    def _get_package_version_fn(self, package_name: str) -> str:
        return self.trigger_side_effect("get_package_version_fn", package_name)
