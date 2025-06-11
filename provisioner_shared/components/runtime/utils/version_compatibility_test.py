#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from provisioner_shared.components.runtime.utils.version_compatibility import VersionCompatibility

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/utils/version_compatibility_test.py
#
class VersionCompatibilityTest(unittest.TestCase):
    """Tests for version compatibility functionality"""

    def test_parse_version_valid_formats(self):
        """Test parsing valid semantic version strings"""
        test_cases = [
            ("1.2.3", (1, 2, 3)),
            ("v1.2.3", (1, 2, 3)),
            ("0.1.0", (0, 1, 0)),
            ("10.20.30", (10, 20, 30)),
            ("1.0.0-alpha", (1, 0, 0)),
            ("2.1.0-beta.1", (2, 1, 0)),
            ("1.2.3+build.1", (1, 2, 3)),
        ]
        
        for version_str, expected in test_cases:
            with self.subTest(version=version_str):
                result = VersionCompatibility.parse_version(version_str)
                self.assertEqual(result, expected)

    def test_parse_version_invalid_formats(self):
        """Test parsing invalid version strings raises ValueError"""
        invalid_versions = ["1.2", "1", "1.2.3.4", "a.b.c", "", "v", "1.2.x"]
        
        for version_str in invalid_versions:
            with self.subTest(version=version_str):
                with self.assertRaises(ValueError):
                    VersionCompatibility.parse_version(version_str)

    def test_exact_version_ranges(self):
        """Test exact version matching"""
        test_cases = [
            ("1.2.3", "1.2.3", True),
            ("1.2.3", "1.2.4", False),
            ("v1.2.3", "1.2.3", True),  # v prefix should be handled
            ("0.1.0", "0.1.0", True),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_compound_version_ranges(self):
        """Test compound version ranges with AND conditions"""
        test_cases = [
            ("1.5.0", ">=1.2.0,<2.0.0", True),
            ("1.1.0", ">=1.2.0,<2.0.0", False),
            ("2.0.0", ">=1.2.0,<2.0.0", False),
            ("1.2.0", ">=1.2.0,<2.0.0", True),
            ("1.9.9", ">=1.2.0,<2.0.0", True),
            ("0.1.15", ">=0.1.10,<0.2.0", True),
            ("0.1.5", ">=0.1.10,<0.2.0", False),
            ("0.2.0", ">=0.1.10,<0.2.0", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_single_condition_ranges(self):
        """Test single condition version ranges"""
        test_cases = [
            ("1.5.0", ">=1.2.0", True),
            ("1.1.0", ">=1.2.0", False),
            ("1.2.0", ">=1.2.0", True),
            ("2.0.0", "<2.0.0", False),
            ("1.9.9", "<2.0.0", True),
            ("1.5.0", ">1.2.0", True),
            ("1.2.0", ">1.2.0", False),
            ("1.5.0", "<=1.5.0", True),
            ("1.5.1", "<=1.5.0", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_tilde_ranges(self):
        """Test tilde range compatibility (~1.2.3 = >=1.2.3,<1.3.0)"""
        test_cases = [
            # ~1.2.3 allows patch updates
            ("1.2.3", "~1.2.3", True),
            ("1.2.4", "~1.2.3", True),
            ("1.2.99", "~1.2.3", True),
            ("1.3.0", "~1.2.3", False),
            ("1.1.99", "~1.2.3", False),
            # ~0.1.10 allows patch updates in 0.x versions
            ("0.1.10", "~0.1.10", True),
            ("0.1.11", "~0.1.10", True),
            ("0.1.9", "~0.1.10", False),
            ("0.2.0", "~0.1.10", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_caret_ranges_major_version_1_plus(self):
        """Test caret range compatibility for versions >= 1.0.0 (^1.2.3 = >=1.2.3,<2.0.0)"""
        test_cases = [
            # ^1.2.3 allows minor and patch updates
            ("1.2.3", "^1.2.3", True),
            ("1.2.4", "^1.2.3", True),
            ("1.3.0", "^1.2.3", True),
            ("1.99.99", "^1.2.3", True),
            ("2.0.0", "^1.2.3", False),
            ("1.1.99", "^1.2.3", False),
            # ^2.0.0 test
            ("2.0.0", "^2.0.0", True),
            ("2.1.0", "^2.0.0", True),
            ("3.0.0", "^2.0.0", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_caret_ranges_major_version_0_minor_non_zero(self):
        """Test caret range compatibility for 0.x.y versions where x > 0 (^0.1.3 = >=0.1.3,<0.2.0)"""
        test_cases = [
            # ^0.1.10 allows only patch updates within the same minor version
            ("0.1.10", "^0.1.10", True),
            ("0.1.11", "^0.1.10", True),
            ("0.1.20", "^0.1.10", True),
            ("0.2.0", "^0.1.10", False),
            ("0.1.9", "^0.1.10", False),
            ("1.0.0", "^0.1.10", False),
            # ^0.9.0 test
            ("0.9.0", "^0.9.0", True),
            ("0.9.5", "^0.9.0", True),
            ("0.10.0", "^0.9.0", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_caret_ranges_major_version_0_minor_zero(self):
        """Test caret range compatibility for 0.0.x versions (^0.0.3 = exact match only)"""
        test_cases = [
            # ^0.0.3 allows only exact match
            ("0.0.3", "^0.0.3", True),
            ("0.0.4", "^0.0.3", False),
            ("0.0.2", "^0.0.3", False),
            ("0.1.0", "^0.0.3", False),
            # ^0.0.1 test
            ("0.0.1", "^0.0.1", True),
            ("0.0.2", "^0.0.1", False),
        ]
        
        for version, range_spec, expected in test_cases:
            with self.subTest(version=version, range=range_spec):
                result = VersionCompatibility.version_satisfies_range(version, range_spec)
                self.assertEqual(result, expected)

    def test_read_plugin_compatibility_with_manifest(self):
        """Test reading plugin compatibility from manifest.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            resources_dir = plugin_dir / "resources"
            resources_dir.mkdir()
            
            manifest_data = {
                "plugin_name": "test_plugin",
                "plugin_version": "1.0.0",
                "runtime_version_range": ">=0.1.10,<0.2.0",
                "description": "Test plugin"
            }
            
            manifest_path = resources_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_data, f)
            
            result = VersionCompatibility.read_plugin_compatibility(str(plugin_dir))
            self.assertEqual(result, ">=0.1.10,<0.2.0")

    def test_read_plugin_compatibility_no_manifest(self):
        """Test reading plugin compatibility when no manifest exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = VersionCompatibility.read_plugin_compatibility(temp_dir)
            self.assertIsNone(result)

    def test_read_plugin_compatibility_invalid_json(self):
        """Test reading plugin compatibility with invalid JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)
            resources_dir = plugin_dir / "resources"
            resources_dir.mkdir()
            
            manifest_path = resources_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                f.write("invalid json content")
            
            result = VersionCompatibility.read_plugin_compatibility(str(plugin_dir))
            self.assertIsNone(result)

    def test_read_runtime_version_from_manifest(self):
        """Test reading runtime version from manifest.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            resources_dir = runtime_dir / "resources"
            resources_dir.mkdir()
            
            manifest_data = {
                "version": "0.1.15",
                "description": "Test runtime"
            }
            
            manifest_path = resources_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_data, f)
            
            result = VersionCompatibility.read_runtime_version(str(runtime_dir))
            self.assertEqual(result, "0.1.15")

    def test_read_runtime_version_from_version_txt(self):
        """Test reading runtime version from version.txt fallback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            resources_dir = runtime_dir / "resources"
            resources_dir.mkdir()
            
            version_path = resources_dir / "version.txt"
            with open(version_path, "w") as f:
                f.write("0.1.16\n")
            
            result = VersionCompatibility.read_runtime_version(str(runtime_dir))
            self.assertEqual(result, "0.1.16")

    def test_read_runtime_version_no_files(self):
        """Test reading runtime version when no version files exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = VersionCompatibility.read_runtime_version(temp_dir)
            self.assertIsNone(result)

    @mock.patch("provisioner_shared.components.runtime.utils.version_compatibility.subprocess.run")
    def test_get_package_version_from_pip_success(self, mock_run):
        """Test getting package version from pip successfully"""
        mock_run.return_value.stdout = "Name: test-package\nVersion: 1.2.3\nSummary: Test"
        
        result = VersionCompatibility.get_package_version_from_pip(["pip"], "test-package")
        self.assertEqual(result, "1.2.3")
        
        mock_run.assert_called_once_with(
            ["pip", "show", "test-package", "--no-color"],
            capture_output=True,
            text=True,
            check=True
        )

    @mock.patch("provisioner_shared.components.runtime.utils.version_compatibility.subprocess.run")
    def test_get_package_version_from_pip_not_found(self, mock_run):
        """Test getting package version from pip when package not found"""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, ["pip", "show", "nonexistent"])
        
        result = VersionCompatibility.get_package_version_from_pip(["pip"], "nonexistent")
        self.assertIsNone(result)

    @mock.patch("provisioner_shared.components.runtime.utils.version_compatibility.subprocess.run")
    def test_get_package_version_from_pip_no_version_line(self, mock_run):
        """Test getting package version from pip when output has no Version line"""
        mock_run.return_value.stdout = "Name: test-package\nSummary: Test package"
        
        result = VersionCompatibility.get_package_version_from_pip(["pip"], "test-package")
        self.assertIsNone(result)

    def test_is_plugin_compatible_no_compatibility_info(self):
        """Test plugin compatibility when no compatibility info is found (assume compatible)"""
        with mock.patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None
            
            result = VersionCompatibility.is_plugin_compatible("nonexistent_plugin", "0.1.15")
            self.assertTrue(result)  # Should assume compatible when package not found

    def test_filter_compatible_plugins(self):
        """Test filtering plugins based on runtime compatibility"""
        plugins = ["plugin1", "plugin2", "plugin3"]
        runtime_version = "0.1.15"
        
        # Mock the is_plugin_compatible method to return specific results
        compatibility_results = [True, False, True]
        
        with mock.patch.object(VersionCompatibility, "is_plugin_compatible") as mock_is_compatible:
            mock_is_compatible.side_effect = compatibility_results
            
            result = VersionCompatibility.filter_compatible_plugins(plugins, runtime_version)
            
            # Should return plugin1 and plugin3 (compatible ones)
            self.assertEqual(result, ["plugin1", "plugin3"])
            
            # Verify all plugins were checked
            expected_calls = [
                mock.call("plugin1", runtime_version),
                mock.call("plugin2", runtime_version),
                mock.call("plugin3", runtime_version),
            ]
            mock_is_compatible.assert_has_calls(expected_calls)

    def test_version_satisfies_range_invalid_version(self):
        """Test version range checking with invalid version strings"""
        with mock.patch("provisioner_shared.components.runtime.utils.version_compatibility.logger") as mock_logger:
            result = VersionCompatibility.version_satisfies_range("invalid.version", ">=1.0.0")
            self.assertFalse(result)
            mock_logger.warning.assert_called()

    def test_version_satisfies_range_invalid_range(self):
        """Test version range checking with invalid range strings"""
        with mock.patch("provisioner_shared.components.runtime.utils.version_compatibility.logger") as mock_logger:
            result = VersionCompatibility.version_satisfies_range("1.0.0", "invalid_range")
            self.assertFalse(result)
            mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main() 