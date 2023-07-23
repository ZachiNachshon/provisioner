#!/usr/bin/env python3

from ..infra.context import Context
from .io_utils import IOUtils
from .properties import Properties


class FakeProperties(Properties):

    registered_properties: dict[str, str] = None

    def __init__(self, io_utils: IOUtils):
        super().__init__(io_utils=io_utils, config_parser=None)
        self.registered_properties = {}

    @staticmethod
    def _create_fake(io_utils: IOUtils) -> "FakeProperties":
        fake_property = FakeProperties(io_utils=io_utils)
        fake_property.read_value_fn = lambda path, key, default=None: fake_property._property_key_selector(key)
        return fake_property

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils) -> "FakeProperties":
        return FakeProperties._create_fake(io_utils=io_utils)

    def register_property_key(self, key: str, expected_value: str):
        # When opting to use the FakeProperties instead of mocking via @mock.patch, we'll override its functions
        self.registered_properties[key] = expected_value

    def _property_key_selector(self, key: str) -> str:
        if key not in self.registered_properties:
            raise LookupError("Fake properties key is not defined. name: " + key)
        return self.registered_properties.get(key)
