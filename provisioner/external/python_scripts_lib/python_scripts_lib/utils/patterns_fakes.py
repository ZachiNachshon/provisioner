#!/usr/bin/env python3

from ..infra.context import Context
from .io_utils import IOUtils
from .patterns import Patterns


class FakePatterns(Patterns):

    registered_patterns: dict[str, str] = None

    def __init__(self, io_utils: IOUtils):
        super().__init__(io_utils=io_utils, config_parser=None)
        self.registered_patterns = {}

    @staticmethod
    def _create_fake(io_utils: IOUtils) -> "FakePatterns":
        fake_patterns = FakePatterns(io_utils=io_utils)
        fake_patterns.resolve_pattern_fn = lambda path, key, *args: fake_patterns._pattern_key_selector(key)
        return fake_patterns

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils) -> "FakePatterns":
        return FakePatterns._create_fake(io_utils=io_utils)

    def register_pattern_key(self, key: str, expected_value: str):
        # When opting to use the FakePatterns instead of mocking via @mock.patch, we'll override the run function
        self.registered_patterns[key] = expected_value

    def _pattern_key_selector(self, key: str) -> str:
        if key not in self.registered_patterns:
            raise LookupError("Fake patterns key is not defined. name: " + key)
        return self.registered_patterns.get(key)
