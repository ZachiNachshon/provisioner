#!/usr/bin/env python3

from unittest.mock import MagicMock

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.randomizer import HashMethod, Randomizer
from provisioner_shared.test_lib.faker import TestFakes


class FakeRandomizer(TestFakes, Randomizer):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        Randomizer.__init__(self, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakeRandomizer":
        fake = FakeRandomizer(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.hash_password_fn = MagicMock(side_effect=fake.hash_password_fn)
        fake.hash_password_sha512_fn = MagicMock(side_effect=fake.hash_password_sha512_fn)
        return fake

    def hash_password_fn(self, password: str, method=HashMethod.SHA256) -> str:
        return self.trigger_side_effect("hash_password_fn", password, method)

    def hash_password_sha512_fn(self, password: str) -> str:
        return self.trigger_side_effect("hash_password_sha512_fn", password)
