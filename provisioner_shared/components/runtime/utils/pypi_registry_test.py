#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_shared.components.runtime.utils.pypi_registry import PyPiRegistry


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/utils/pypi_registry_test.py
#
class PyPiRegistryTest(unittest.TestCase):
    """Tests for PyPiRegistry functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_http_client = mock.Mock()
        self.pypi_registry = PyPiRegistry(self.mock_http_client)

    def test_get_package_version_success(self):
        """Test successful package version retrieval from PyPI"""
        mock_response_json = '{"info": {"version": "1.2.3"}}'
        self.mock_http_client.get_fn.return_value = mock_response_json

        result = self.pypi_registry._get_package_version("test-package")

        self.assertEqual(result, "1.2.3")
        self.mock_http_client.get_fn.assert_called_once_with("https://pypi.org/pypi/test-package/json", timeout=10)

    def test_get_package_version_not_found(self):
        """Test package version retrieval when package is not found"""
        self.mock_http_client.get_fn.side_effect = Exception("404 Client Error")

        result = self.pypi_registry._get_package_version("nonexistent-package")

        self.assertIsNone(result)
        self.mock_http_client.get_fn.assert_called_once_with(
            "https://pypi.org/pypi/nonexistent-package/json", timeout=10
        )

    def test_get_package_version_timeout(self):
        """Test package version retrieval when request times out"""
        self.mock_http_client.get_fn.side_effect = Exception("Request timed out")

        result = self.pypi_registry._get_package_version("slow-package")

        self.assertIsNone(result)
        self.mock_http_client.get_fn.assert_called_once_with("https://pypi.org/pypi/slow-package/json", timeout=10)

    def test_get_package_version_connection_error(self):
        """Test package version retrieval when connection fails"""
        self.mock_http_client.get_fn.side_effect = Exception("Connection failed")

        result = self.pypi_registry._get_package_version("unreachable-package")

        self.assertIsNone(result)
        self.mock_http_client.get_fn.assert_called_once_with(
            "https://pypi.org/pypi/unreachable-package/json", timeout=10
        )

    def test_get_package_version_invalid_response(self):
        """Test package version retrieval when response format is invalid"""
        mock_response_json = '{"info": {}}'  # Missing version field
        self.mock_http_client.get_fn.return_value = mock_response_json

        result = self.pypi_registry._get_package_version("invalid-response-package")

        self.assertIsNone(result)
        self.mock_http_client.get_fn.assert_called_once_with(
            "https://pypi.org/pypi/invalid-response-package/json", timeout=10
        )

    def test_get_package_version_json_decode_error(self):
        """Test package version retrieval when JSON decoding fails"""
        self.mock_http_client.get_fn.return_value = "invalid json content"

        result = self.pypi_registry._get_package_version("malformed-json-package")

        self.assertIsNone(result)
        self.mock_http_client.get_fn.assert_called_once_with(
            "https://pypi.org/pypi/malformed-json-package/json", timeout=10
        )

    @mock.patch("provisioner_shared.components.runtime.utils.pypi_registry.logger")
    def test_get_package_version_logs_errors(self, mock_logger):
        """Test that errors are properly logged"""
        self.mock_http_client.get_fn.side_effect = Exception("404 Client Error")

        result = self.pypi_registry._get_package_version("test-package")

        self.assertIsNone(result)
        mock_logger.debug.assert_called()

    def test_get_package_version_empty_package_name(self):
        """Test package version retrieval with empty package name"""
        result = self.pypi_registry._get_package_version("")
        # The method should still try to make a request, but fail
        self.assertIsNone(result)

    def test_get_package_version_none_package_name(self):
        """Test package version retrieval with None package name"""
        # Should handle None gracefully and return None
        result = self.pypi_registry._get_package_version(None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
