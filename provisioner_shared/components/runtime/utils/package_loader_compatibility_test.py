#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_shared.components.runtime.utils.package_loader import PackageLoader


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/utils/package_loader_compatibility_test.py
#
class PackageLoaderCompatibilityTest(unittest.TestCase):
    """Tests for PackageLoader version compatibility functionality"""

    def setUp(self):
        """Set up test fixtures"""
        from provisioner_shared.components.runtime.cli.modifiers import PackageManager

        self.mock_ctx = mock.Mock()
        self.mock_ctx.get_package_manager.return_value = PackageManager.PIP
        self.mock_io_utils = mock.Mock()
        self.mock_process = mock.Mock()
        self.mock_pypi_registry = mock.Mock()

        self.loader = PackageLoader(
            ctx=self.mock_ctx, io_utils=self.mock_io_utils, process=self.mock_process, pypi=self.mock_pypi_registry
        )

    @mock.patch(
        "provisioner_shared.components.runtime.utils.package_loader.VersionCompatibility.get_package_version_from_pip"
    )
    def test_get_runtime_version_from_pip_success(self, mock_get_version):
        """Test getting runtime version from pip package"""
        mock_get_version.return_value = "0.1.15"

        result = self.loader._get_runtime_version()

        self.assertEqual(result, "0.1.15")

    def test_get_runtime_version_from_manifest_file(self):
        """Test getting runtime version from manifest.json file"""
        # Mock pip method failing
        with mock.patch(
            "provisioner_shared.components.runtime.utils.package_loader.VersionCompatibility.get_package_version_from_pip"
        ) as mock_pip:
            mock_pip.return_value = None
            # Mock io_utils to return manifest content
            self.mock_io_utils.read_file_safe_fn.side_effect = [
                '{"version": "0.1.16"}',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]

            result = self.loader._get_runtime_version()

            self.assertEqual(result, "0.1.16")

    def test_get_runtime_version_from_pypi_fallback(self):
        """Test getting runtime version from PyPI as fallback"""
        # Mock pip method failing
        with mock.patch(
            "provisioner_shared.components.runtime.utils.package_loader.VersionCompatibility.get_package_version_from_pip"
        ) as mock_pip:
            mock_pip.return_value = None
            # Mock all local manifest.json files failing
            self.mock_io_utils.read_file_safe_fn.return_value = None
            # Mock PyPI registry success
            self.mock_pypi_registry._get_package_version_fn.return_value = "0.1.17"

            result = self.loader._get_runtime_version()

            self.assertEqual(result, "0.1.17")
            self.mock_pypi_registry._get_package_version_fn.assert_called_once_with("provisioner-runtime")

    def test_get_runtime_version_all_methods_fail(self):
        """Test runtime version detection when all methods fail"""
        # Mock all methods failing
        with mock.patch(
            "provisioner_shared.components.runtime.utils.package_loader.VersionCompatibility.get_package_version_from_pip"
        ) as mock_pip:
            mock_pip.return_value = None
            # Mock all local manifest.json files failing
            self.mock_io_utils.read_file_safe_fn.return_value = None
            self.mock_pypi_registry._get_package_version_fn.return_value = None

            result = self.loader._get_runtime_version()

            self.assertIsNone(result)

    def test_load_modules_with_version_check_fn_compatible_plugins(self):
        """Test loading modules with version compatibility filtering"""
        with mock.patch.object(self.loader, "_get_runtime_version") as mock_get_runtime_version:
            mock_get_runtime_version.return_value = "0.1.15"

            # Mock the load_modules_fn to simulate loading plugins
            with mock.patch.object(self.loader, "_load_modules") as mock_load_modules:
                # Call the version check method directly
                self.loader._load_modules_with_auto_version_check(
                    filter_keyword="provisioner", import_path="main", exclusions=[], callback=None, debug=False
                )

                # Verify that _load_modules was called with version filtering enabled
                mock_load_modules.assert_called_once_with(
                    filter_keyword="provisioner",
                    import_path="main",
                    exclusions=[],
                    callback=None,
                    debug=False,
                    enable_version_filtering=True,
                    runtime_version="0.1.15",
                )

    def test_load_modules_with_version_check_fn_no_runtime_version(self):
        """Test loading modules when runtime version cannot be determined"""
        with mock.patch.object(self.loader, "_get_runtime_version") as mock_get_runtime_version:
            mock_get_runtime_version.return_value = None

            with mock.patch.object(self.loader, "_load_modules") as mock_load_modules:
                # Call the version check method directly
                self.loader._load_modules_with_auto_version_check(filter_keyword="provisioner", import_path="main")

                # Verify that _load_modules was called with version filtering enabled but no runtime version
                mock_load_modules.assert_called_once_with(
                    filter_keyword="provisioner",
                    import_path="main",
                    exclusions=[],
                    callback=None,
                    debug=False,
                    enable_version_filtering=True,
                    runtime_version=None,
                )

    def test_load_modules_with_version_check_fn_returns_callable(self):
        """Test that load_modules_with_version_check_fn returns a callable function"""
        version_check_fn = self.loader.load_modules_with_auto_version_check_fn
        self.assertTrue(callable(version_check_fn))

    def test_runtime_version_caching(self):
        """Test that runtime version is cached after first retrieval"""
        with mock.patch(
            "provisioner_shared.components.runtime.utils.package_loader.VersionCompatibility.get_package_version_from_pip"
        ) as mock_pip:
            mock_pip.return_value = "0.1.15"

            # First call should query pip
            result1 = self.loader._get_runtime_version()
            self.assertEqual(result1, "0.1.15")

            # Second call should use cached value (pip not called again)
            result2 = self.loader._get_runtime_version()
            self.assertEqual(result2, "0.1.15")

            # Verify pip was only called once (caching works)
            self.assertEqual(mock_pip.call_count, 1)


if __name__ == "__main__":
    unittest.main()
