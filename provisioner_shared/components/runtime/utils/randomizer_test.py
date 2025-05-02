#!/usr/bin/env python3

import unittest

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.randomizer import HashMethod, Randomizer
from provisioner_shared.components.runtime.utils.randomizer_fakes import FakeRandomizer


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/utils/randomizer_test.py
#
class RandomizerTest(unittest.TestCase):
    def setUp(self):
        self.ctx = Context.create()
        self.randomizer = Randomizer.create(self.ctx)
        self.fake_randomizer = FakeRandomizer.create(self.ctx)

    def test_hash_password(self):
        # Test with default SHA256
        password = "s3cret"
        hashed_password = self.randomizer.hash_password_fn(password)

        # Check format compliance with shadow/crypt format
        self.assertTrue(hashed_password.startswith("$5$"))
        parts = hashed_password.split("$")
        self.assertEqual(len(parts), 4)  # Format: $5$salt$hash

        # Test with explicitly specified SHA-512
        hashed_password_512 = self.randomizer.hash_password_fn(password, HashMethod.SHA512)

        # Check format compliance with shadow/crypt format
        self.assertTrue(hashed_password_512.startswith("$6$"))
        parts = hashed_password_512.split("$")
        self.assertEqual(len(parts), 4)  # Format: $6$salt$hash

        #
        # TODO: Fix me - should adjust the fake implementation to match the signature of the method
        #
        # Test with fake implementation
        # fake_result = "mocked_hashed_password"
        # self.fake_randomizer.on("hash_password_fn", str, Anything).return_value = fake_result
        # result = self.fake_randomizer.hash_password_fn("any_password", HashMethod.SHA256)
        # self.assertEqual(result, fake_result)

    def test_dry_run_hash_password(self):
        dry_run_ctx = Context.create(dry_run=True)
        dry_run_randomizer = Randomizer.create(dry_run_ctx)

        password = "testpassword"

        # Test SHA256 (default)
        result_256 = dry_run_randomizer.hash_password_fn(password)
        self.assertEqual(result_256, f"DRY_RUN_SHA256_HASH_{password}")

        # Test SHA512
        result_512 = dry_run_randomizer.hash_password_fn(password, HashMethod.SHA512)
        self.assertEqual(result_512, f"DRY_RUN_SHA512_HASH_{password}")
