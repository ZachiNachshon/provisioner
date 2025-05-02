#!/usr/bin/env python3

import unittest

from provisioner_shared.components.runtime.domain.serialize import SerializationBase


# To run these directly from the terminal use:
#  ./run_tests.py provisioner_shared/components/runtime/domain/serialize_test.py
#
class DummySerializationBase(SerializationBase):
    """Concrete implementation of the abstract SerializationBase class for testing."""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict) -> None:
        """Implementation of abstract method."""
        pass

    def merge(self, other: SerializationBase) -> SerializationBase:
        """Implementation of abstract method."""
        return self


class TestSerializeBase(unittest.TestCase):

    def test_maybe_get_primitive_values(self):
        """Test that maybe_get correctly returns primitive values."""
        test_data = {
            "string_value": "test",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "none_value": None,
            "nested": {"deep_string": "nested string", "deep_int": 100},
        }

        serializer = DummySerializationBase(test_data)

        # Test getting primitive values
        self.assertEqual(serializer.maybe_get("string_value"), "test")
        self.assertEqual(serializer.maybe_get("int_value"), 42)
        self.assertEqual(serializer.maybe_get("float_value"), 3.14)
        self.assertEqual(serializer.maybe_get("bool_value"), True)
        self.assertIsNone(serializer.maybe_get("none_value"))

        # Test getting nested primitive values
        self.assertEqual(serializer.maybe_get("nested.deep_string"), "nested string")
        self.assertEqual(serializer.maybe_get("nested.deep_int"), 100)

    def test_maybe_get_missing_keys(self):
        """Test that maybe_get returns None for missing keys."""
        test_data = {"a": {"b": "value"}}
        serializer = DummySerializationBase(test_data)

        # Test with non-existent keys
        self.assertIsNone(serializer.maybe_get("non_existent"))
        self.assertIsNone(serializer.maybe_get("a.non_existent"))
        self.assertIsNone(serializer.maybe_get("a.b.non_existent"))

    def test_maybe_get_non_primitive_values(self):
        """Test that maybe_get returns None for non-primitive values."""
        test_data = {
            "dict_value": {"key": "value"},
            "list_value": [1, 2, 3],
            "nested_with_dict": {"dict_inside": {"more": "data"}},
        }

        serializer = DummySerializationBase(test_data)

        # Test getting dictionary values (should return None)
        self.assertIsNone(serializer.maybe_get("dict_value"))

        # Test getting list values (should return None)
        self.assertIsNone(serializer.maybe_get("list_value"))

        # Test getting nested dictionary values (should return None)
        self.assertIsNone(serializer.maybe_get("nested_with_dict"))
        self.assertIsNone(serializer.maybe_get("nested_with_dict.dict_inside"))

    def test_maybe_get_complex_paths(self):
        """Test maybe_get with complex nested paths."""
        test_data = {"level1": {"level2": {"level3": {"primitive": "deep value", "another_dict": {"key": "value"}}}}}

        serializer = DummySerializationBase(test_data)

        # Deep primitive value should be returned
        self.assertEqual(serializer.maybe_get("level1.level2.level3.primitive"), "deep value")

        # Deep non-primitive value should return None
        self.assertIsNone(serializer.maybe_get("level1.level2.level3.another_dict"))

        # Partial path to a dictionary should return None
        self.assertIsNone(serializer.maybe_get("level1.level2"))
