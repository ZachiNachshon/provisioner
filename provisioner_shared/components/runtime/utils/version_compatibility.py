#!/usr/bin/env python3

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


class VersionCompatibility:
    """
    Utility class for checking version compatibility between runtime and plugins.
    Uses semantic versioning and version ranges to determine compatibility.
    """

    @staticmethod
    def parse_version(version: str) -> Tuple[int, int, int]:
        """
        Parse a semantic version string into major, minor, patch components.

        Args:
            version: Version string like "1.2.3"

        Returns:
            Tuple of (major, minor, patch) as integers

        Raises:
            ValueError: If version format is invalid
        """
        # Remove 'v' prefix if present and strip whitespace
        clean_version = version.strip().lstrip("v")

        # Match semantic version pattern
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$", clean_version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")

        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    @staticmethod
    def version_satisfies_range(version: str, version_range: str) -> bool:
        """
        Check if a version satisfies a version range specification.

        Supported range formats:
        - ">=1.0.0,<2.0.0" (AND condition)
        - ">=1.0.0" (minimum version)
        - "~1.2.0" (compatible within patch level, equivalent to >=1.2.0,<1.3.0)
        - "^1.2.0" (compatible within minor level, equivalent to >=1.2.0,<2.0.0)
        - "1.2.3" (exact version)

        Args:
            version: Version to check
            version_range: Range specification

        Returns:
            True if version satisfies the range, False otherwise
        """
        try:
            version_tuple = VersionCompatibility.parse_version(version)

            # Handle exact version
            if not any(op in version_range for op in [">=", "<=", ">", "<", "~", "^", ","]):
                try:
                    range_tuple = VersionCompatibility.parse_version(version_range)
                    return version_tuple == range_tuple
                except ValueError:
                    logger.warning(f"Invalid exact version range: {version_range}")
                    return False

            # Handle caret range (^1.2.0 = >=1.2.0,<2.0.0)
            if version_range.startswith("^"):
                base_version = version_range[1:]
                base_tuple = VersionCompatibility.parse_version(base_version)
                major, minor, patch = base_tuple

                return version_tuple >= base_tuple and version_tuple < (major + 1, 0, 0)

            # Handle tilde range (~1.2.0 = >=1.2.0,<1.3.0)
            if version_range.startswith("~"):
                base_version = version_range[1:]
                base_tuple = VersionCompatibility.parse_version(base_version)
                major, minor, patch = base_tuple

                return version_tuple >= base_tuple and version_tuple < (major, minor + 1, 0)

            # Handle compound ranges (>=1.0.0,<2.0.0)
            if "," in version_range:
                conditions = [cond.strip() for cond in version_range.split(",")]
                return all(VersionCompatibility._check_single_condition(version_tuple, cond) for cond in conditions)

            # Handle single condition
            return VersionCompatibility._check_single_condition(version_tuple, version_range)

        except ValueError as e:
            logger.warning(f"Error parsing version compatibility: {e}")
            return False

    @staticmethod
    def _check_single_condition(version_tuple: Tuple[int, int, int], condition: str) -> bool:
        """Check a single version condition like '>=1.0.0' or '<2.0.0'"""
        condition = condition.strip()

        # Extract operator and version
        for op in [">=", "<=", ">", "<", "="]:
            if condition.startswith(op):
                op_version = condition[len(op) :].strip()
                try:
                    op_tuple = VersionCompatibility.parse_version(op_version)

                    if op == ">=":
                        return version_tuple >= op_tuple
                    elif op == "<=":
                        return version_tuple <= op_tuple
                    elif op == ">":
                        return version_tuple > op_tuple
                    elif op == "<":
                        return version_tuple < op_tuple
                    elif op == "=":
                        return version_tuple == op_tuple

                except ValueError:
                    logger.warning(f"Invalid version in condition: {op_version}")
                    return False
                break
        else:
            logger.warning(f"Unknown condition format: {condition}")
            return False

        return False

    @staticmethod
    def read_plugin_compatibility(plugin_package_path: str) -> Optional[str]:
        """
        Read the runtime compatibility range from a plugin's metadata file.

        Args:
            plugin_package_path: Path to the plugin package directory

        Returns:
            Version range string if found, None otherwise
        """
        try:
            # Try to read from plugin-manifest.json first
            manifest_path = Path(plugin_package_path) / "resources" / "plugin-manifest.json"
            if manifest_path.exists():
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                    return manifest.get("runtime_version_range")

            # Fallback: try to read from compatibility.txt
            compat_path = Path(plugin_package_path) / "resources" / "compatibility.txt"
            if compat_path.exists():
                with open(compat_path, "r") as f:
                    return f.read().strip()

        except Exception as e:
            logger.debug(f"Could not read plugin compatibility from {plugin_package_path}: {e}")

        return None

    @staticmethod
    def read_runtime_version(runtime_package_path: str) -> Optional[str]:
        """
        Read the current runtime version.

        Args:
            runtime_package_path: Path to the runtime package directory

        Returns:
            Version string if found, None otherwise
        """
        try:
            version_path = Path(runtime_package_path) / "resources" / "version.txt"
            if version_path.exists():
                with open(version_path, "r") as f:
                    return f.read().strip()
        except Exception as e:
            logger.debug(f"Could not read runtime version from {runtime_package_path}: {e}")

        return None

    @staticmethod
    def get_package_version_from_pip(pip_cmd: List[str], package_name: str) -> Optional[str]:
        """
        Get the version of an installed pip package.

        Args:
            package_name: Name of the pip package

        Returns:
            Version string if package is installed, None otherwise
        """
        try:
            result = subprocess.run(
                pip_cmd + ["show", package_name, "--no-color"], capture_output=True, text=True, check=True
            )

            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Could not get pip package version for {package_name}: {e}")

        return None

    @staticmethod
    def is_plugin_compatible(plugin_package_name: str, runtime_version: str) -> bool:
        """
        Check if a plugin is compatible with the current runtime version.

        Args:
            plugin_package_name: Name of the plugin package (e.g., "provisioner_installers_plugin")
            runtime_version: Current runtime version

        Returns:
            True if compatible or no compatibility info found (assume compatible),
            False if explicitly incompatible
        """
        try:
            # Try to get plugin path from installed package
            import importlib.util

            # Convert package name format (provisioner-installers-plugin -> provisioner_installers_plugin)
            normalized_name = plugin_package_name.replace("-", "_")

            spec = importlib.util.find_spec(normalized_name)
            if spec is None or spec.origin is None:
                logger.debug(f"Could not find plugin package: {normalized_name}")
                return True  # Assume compatible if can't find package

            # Get plugin package directory
            plugin_path = Path(spec.origin).parent

            # Read compatibility range
            version_range = VersionCompatibility.read_plugin_compatibility(str(plugin_path))

            if version_range is None:
                logger.debug(f"No compatibility info found for {plugin_package_name}, assuming compatible")
                return True  # No compatibility info means assume compatible

            is_compatible = VersionCompatibility.version_satisfies_range(runtime_version, version_range)

            logger.debug(
                f"Plugin {plugin_package_name} compatibility check: "
                f"runtime={runtime_version}, range={version_range}, compatible={is_compatible}"
            )

            return is_compatible

        except Exception as e:
            logger.warning(f"Error checking plugin compatibility for {plugin_package_name}: {e}")
            return True  # Assume compatible on error

    @staticmethod
    def filter_compatible_plugins(plugin_packages: List[str], runtime_version: str) -> List[str]:
        """
        Filter a list of plugin packages to only include those compatible with the runtime version.

        Args:
            plugin_packages: List of plugin package names
            runtime_version: Current runtime version

        Returns:
            Filtered list of compatible plugin packages
        """
        if not runtime_version:
            logger.warning("No runtime version provided, returning all plugins")
            return plugin_packages

        compatible_plugins = []

        for plugin_package in plugin_packages:
            if VersionCompatibility.is_plugin_compatible(plugin_package, runtime_version):
                compatible_plugins.append(plugin_package)
            else:
                logger.debug(f"Skipping incompatible plugin: {plugin_package}")

        return compatible_plugins
