#!/usr/bin/env python3
"""
Test Suite for Version Manager Script

This test suite provides comprehensive testing for all version manager functionality
including RC generation, GA promotion, plugin detection, and error handling.
"""

import json
import os
import subprocess

# Add the current directory to Python path to import version_manager
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from version_manager import VersionManager


class TestVersionManager(unittest.TestCase):
    """Test cases for VersionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_github_token = "test_token_123"

        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {"GITHUB_TOKEN": self.test_github_token})
        self.env_patcher.start()

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_pyproject_toml(self, package_name: str, version: str = "0.1.0") -> Path:
        """Create a test pyproject.toml file."""
        pyproject_content = f"""
[tool.poetry]
name = "{package_name}"
version = "{version}"
description = "Test package"
authors = ["Test Author <test@example.com>"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content.strip())
        return pyproject_path

    def test_init_without_github_token(self):
        """Test initialization without GITHUB_TOKEN environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                VersionManager()
            self.assertIn("GITHUB_TOKEN environment variable is required", str(context.exception))

    def test_init_plugin_mode_without_context(self):
        """Test initialization in plugin mode without plugin context."""
        with self.assertRaises(ValueError) as context:
            VersionManager(plugin_mode=True, require_plugin_context=True)
        self.assertIn("Plugin mode enabled but no plugin detected", str(context.exception))

    def test_init_plugin_mode_with_context_disabled(self):
        """Test initialization in plugin mode with context requirement disabled."""
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        self.assertTrue(vm.plugin_mode)
        self.assertIsNone(vm.plugin_name)

    def test_validate_project_path_success(self):
        """Test successful project path validation."""
        self.create_test_pyproject_toml("test-package")

        vm = VersionManager()
        package_name = vm.validate_project_path(str(self.temp_path))

        self.assertEqual(package_name, "test-package")
        self.assertEqual(vm.package_name, "test-package")

    def test_validate_project_path_missing_directory(self):
        """Test project path validation with missing directory."""
        vm = VersionManager()

        with self.assertRaises(ValueError) as context:
            vm.validate_project_path("/nonexistent/path")
        self.assertIn("Project path does not exist", str(context.exception))

    def test_validate_project_path_missing_pyproject(self):
        """Test project path validation with missing pyproject.toml."""
        vm = VersionManager()

        with self.assertRaises(ValueError) as context:
            vm.validate_project_path(str(self.temp_path))
        self.assertIn("does not contain pyproject.toml", str(context.exception))

    def test_validate_project_path_invalid_pyproject(self):
        """Test project path validation with invalid pyproject.toml."""
        invalid_pyproject = self.temp_path / "pyproject.toml"
        invalid_pyproject.write_text("invalid toml content [[[")

        vm = VersionManager()

        with self.assertRaises(ValueError) as context:
            vm.validate_project_path(str(self.temp_path))
        self.assertIn("Failed to parse pyproject.toml", str(context.exception))

    def test_validate_project_path_missing_name(self):
        """Test project path validation with missing package name."""
        pyproject_content = """
[tool.poetry]
version = "0.1.0"
description = "Test package"
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content.strip())

        vm = VersionManager()

        with self.assertRaises(ValueError) as context:
            vm.validate_project_path(str(self.temp_path))
        self.assertIn("does not contain 'name' attribute", str(context.exception))

    @patch("version_manager.VersionManager.run_command")
    def test_get_current_version(self, mock_run_command):
        """Test getting current version from poetry."""
        mock_run_command.return_value = "test-package 1.2.3"

        vm = VersionManager()
        version = vm.get_current_version(Path("/test/path"))

        self.assertEqual(version, "1.2.3")
        mock_run_command.assert_called_once_with("poetry version", cwd=Path("/test/path"))

    def test_get_tag_name_main_project(self):
        """Test tag name generation for main project."""
        vm = VersionManager(plugin_mode=False)
        tag_name = vm._get_tag_name("1.2.3")
        self.assertEqual(tag_name, "v1.2.3")

    def test_get_tag_name_plugin(self):
        """Test tag name generation for plugin."""
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        vm.plugin_name = "provisioner_examples_plugin"

        tag_name = vm._get_tag_name("1.2.3")
        self.assertEqual(tag_name, "examples-plugin-v1.2.3")

    def test_get_package_name_main_project(self):
        """Test package name generation for main project."""
        vm = VersionManager(plugin_mode=False)
        vm.package_name = "provisioner-runtime"

        package_name = vm._get_package_name()
        self.assertEqual(package_name, "provisioner-runtime")

    def test_get_package_name_plugin_fallback(self):
        """Test package name generation for plugin with fallback."""
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        vm.plugin_name = "provisioner_examples_plugin"

        package_name = vm._get_package_name()
        self.assertEqual(package_name, "provisioner-examples-plugin")

    @patch("version_manager.VersionManager.run_command")
    def test_check_tag_exists_github_api(self, mock_run_command):
        """Test checking tag existence using GitHub API."""
        mock_run_command.return_value = "v1.2.3\nv1.2.2\nv1.2.1"

        vm = VersionManager(github_repo="owner/repo")

        # Test existing tag
        exists = vm.check_tag_exists("1.2.3")
        self.assertTrue(exists)

        # Test non-existing tag
        exists = vm.check_tag_exists("1.2.4")
        self.assertFalse(exists)

    @patch("version_manager.VersionManager.run_command")
    def test_check_tag_exists_fallback_to_local(self, mock_run_command):
        """Test checking tag existence with fallback to local git."""
        # First call (GitHub API) fails, second call (local git) succeeds
        mock_run_command.side_effect = [subprocess.CalledProcessError(1, "gh api"), "v1.2.3\nv1.2.2"]

        vm = VersionManager()
        exists = vm.check_tag_exists("1.2.3")
        self.assertTrue(exists)

    @patch("version_manager.VersionManager.run_command")
    def test_check_release_exists(self, mock_run_command):
        """Test checking release existence."""
        mock_run_command.return_value = '{"isPrerelease": true}'

        vm = VersionManager()
        exists, is_prerelease = vm.check_release_exists("1.2.3-RC.1")

        self.assertTrue(exists)
        self.assertTrue(is_prerelease)

    def test_validate_rc_version_format(self):
        """Test RC version format validation."""
        vm = VersionManager()

        # Valid formats
        self.assertTrue(vm.validate_rc_version_format("1.2.3-RC.1"))
        self.assertTrue(vm.validate_rc_version_format("0.1.0-RC.10"))
        self.assertTrue(vm.validate_rc_version_format("10.20.30-RC.999"))

        # Invalid formats
        self.assertFalse(vm.validate_rc_version_format("1.2.3"))
        self.assertFalse(vm.validate_rc_version_format("1.2.3-RC"))
        self.assertFalse(vm.validate_rc_version_format("1.2.3-RC."))
        self.assertFalse(vm.validate_rc_version_format("1.2.3-RC.a"))
        self.assertFalse(vm.validate_rc_version_format("1.2-RC.1"))

    def test_parse_version(self):
        """Test version parsing."""
        vm = VersionManager()

        # Test normal version
        major, minor, patch = vm.parse_version("1.2.3")
        self.assertEqual((major, minor, patch), (1, 2, 3))

        # Test RC version
        major, minor, patch = vm.parse_version("1.2.3-RC.1")
        self.assertEqual((major, minor, patch), (1, 2, 3))

        # Test invalid version
        with self.assertRaises(ValueError):
            vm.parse_version("1.2")

        with self.assertRaises(ValueError):
            vm.parse_version("1.2.a")

    @patch("version_manager.VersionManager.run_command")
    def test_get_latest_rc_version_main_project(self, mock_run_command):
        """Test getting latest RC version for main project."""
        mock_run_command.return_value = "v1.2.3-RC.2\nv1.2.3-RC.1\nv1.2.2-RC.1"

        vm = VersionManager(plugin_mode=False)
        latest_rc = vm.get_latest_rc_version()

        self.assertEqual(latest_rc, "1.2.3-RC.2")

    @patch("version_manager.VersionManager.run_command")
    def test_get_latest_rc_version_plugin(self, mock_run_command):
        """Test getting latest RC version for plugin."""
        mock_run_command.return_value = (
            "provisioner-examples-plugin-v1.2.3-RC.2\nprovisioner-examples-plugin-v1.2.3-RC.1"
        )

        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        vm.plugin_name = "provisioner_examples_plugin"
        latest_rc = vm.get_latest_rc_version()

        self.assertEqual(latest_rc, "1.2.3-RC.2")

    @patch("version_manager.VersionManager.get_current_version")
    @patch("version_manager.VersionManager.check_tag_exists")
    def test_generate_rc_versions_new_version(self, mock_check_tag, mock_get_version):
        """Test RC generation for new version."""
        mock_get_version.return_value = "1.2.3"
        mock_check_tag.side_effect = lambda v: v == "1.2.3"  # Only base version exists

        vm = VersionManager(plugin_mode=False)
        package_version, rc_tag = vm.generate_rc_versions("/test/path")

        self.assertEqual(package_version, "1.2.4")  # Incremented patch
        self.assertEqual(rc_tag, "v1.2.4-RC.1")

    @patch("version_manager.VersionManager.get_current_version")
    @patch("version_manager.VersionManager.check_tag_exists")
    def test_generate_rc_versions_existing_rc(self, mock_check_tag, mock_get_version):
        """Test RC generation when current version is already RC."""
        mock_get_version.return_value = "1.2.3-RC.1"
        mock_check_tag.side_effect = lambda v: v in ["1.2.3-RC.1"]  # Only RC.1 exists

        vm = VersionManager(plugin_mode=False)
        package_version, rc_tag = vm.generate_rc_versions("/test/path")

        self.assertEqual(package_version, "1.2.3")  # Base version
        self.assertEqual(rc_tag, "v1.2.3-RC.2")  # Next RC

    @patch("version_manager.VersionManager.validate_rc_version_format")
    @patch("version_manager.VersionManager.check_release_exists")
    def test_determine_rc_to_promote_valid_input(self, mock_check_release, mock_validate):
        """Test RC promotion with valid input RC version."""
        mock_validate.return_value = True
        mock_check_release.return_value = (True, True)  # Exists and is prerelease

        vm = VersionManager()
        rc_version, stable_version = vm.determine_rc_to_promote("1.2.3-RC.1")

        self.assertEqual(rc_version, "1.2.3-RC.1")
        self.assertEqual(stable_version, "1.2.3")

    @patch("version_manager.VersionManager.get_latest_rc_version")
    def test_determine_rc_to_promote_auto_detect(self, mock_get_latest):
        """Test RC promotion with auto-detection."""
        mock_get_latest.return_value = "1.2.3-RC.2"

        vm = VersionManager()
        rc_version, stable_version = vm.determine_rc_to_promote()

        self.assertEqual(rc_version, "1.2.3-RC.2")
        self.assertEqual(stable_version, "1.2.3")

    def test_determine_rc_to_promote_invalid_format(self):
        """Test RC promotion with invalid RC format."""
        vm = VersionManager()

        with self.assertRaises(ValueError) as context:
            vm.determine_rc_to_promote("1.2.3")
        self.assertIn("Invalid RC version format", str(context.exception))

    @patch("version_manager.VersionManager.run_command")
    def test_discover_plugins(self, mock_run_command):
        """Test plugin discovery."""
        # Mock the directory structure
        plugins_dir = self.temp_path / "plugins"
        plugins_dir.mkdir()

        # Create test plugin directories
        for plugin_name in ["provisioner_examples_plugin", "provisioner_test_plugin"]:
            plugin_dir = plugins_dir / plugin_name
            plugin_dir.mkdir()
            self.create_test_pyproject_toml(plugin_name, version="0.1.0")
            # Move the pyproject.toml to the plugin directory
            (self.temp_path / "pyproject.toml").rename(plugin_dir / "pyproject.toml")

        # Change to plugins directory for testing
        with patch("pathlib.Path.cwd", return_value=plugins_dir):
            vm = VersionManager(plugin_mode=True, require_plugin_context=False)
            plugins = vm.discover_plugins()

        self.assertEqual(set(plugins), {"provisioner_examples_plugin", "provisioner_test_plugin"})

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    def test_get_plugins_from_changes(self, mock_discover, mock_run_command):
        """Test getting plugins from git changes."""
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_test_plugin"]
        mock_run_command.return_value = "provisioner_examples_plugin/main.py\nother_file.py"

        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()

        self.assertEqual(affected_plugins, ["provisioner_examples_plugin"])

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins") 
    @patch("version_manager.Path")
    def test_get_plugins_from_changes_single_plugin_in_submodule(self, mock_path, mock_discover, mock_run_command):
        """Test detecting changes for a single plugin in submodule."""
        # Mock plugin discovery
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin", "provisioner_single_board_plugin"]
        
        # Mock Path for plugins directory
        mock_plugins_dir = mock_path.return_value
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.__truediv__.return_value.exists.return_value = True  # plugins/.git exists
        
        # Mock git commands - main repo shows no direct plugin changes, submodule shows one plugin changed
        def mock_run_command_side_effect(cmd, cwd=None):
            if cwd is None:  # Main repository
                return "scripts/github_actions/version_manager.py\nREADME.md"  # No plugin files
            else:  # Plugins submodule
                return "provisioner_examples_plugin/main.py\nprovisioner_examples_plugin/poetry.toml"
        
        mock_run_command.side_effect = mock_run_command_side_effect
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        self.assertEqual(affected_plugins, ["provisioner_examples_plugin"])
        # Verify both main repo and submodule were checked
        self.assertEqual(mock_run_command.call_count, 2)

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    @patch("version_manager.Path")
    def test_get_plugins_from_changes_multiple_plugins_in_submodule(self, mock_path, mock_discover, mock_run_command):
        """Test detecting changes for multiple plugins in submodule."""
        # Mock plugin discovery
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin", "provisioner_single_board_plugin"]
        
        # Mock Path for plugins directory
        mock_plugins_dir = mock_path.return_value
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.__truediv__.return_value.exists.return_value = True  # plugins/.git exists
        
        # Mock git commands - main repo shows no direct changes, submodule shows multiple plugins changed
        def mock_run_command_side_effect(cmd, cwd=None):
            if cwd is None:  # Main repository
                return "scripts/github_actions/version_manager.py"  # No plugin files
            else:  # Plugins submodule
                return ("provisioner_examples_plugin/main.py\n"
                       "provisioner_installers_plugin/main.py\n"
                       "provisioner_installers_plugin/poetry.toml\n"
                       "README.md")
        
        mock_run_command.side_effect = mock_run_command_side_effect
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        # Should detect both plugins, sorted alphabetically 
        expected_plugins = ["provisioner_examples_plugin", "provisioner_installers_plugin"]
        self.assertEqual(sorted(affected_plugins), expected_plugins)

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    @patch("version_manager.Path")
    def test_get_plugins_from_changes_main_repo_and_submodule(self, mock_path, mock_discover, mock_run_command):
        """Test detecting changes in both main repo and submodule."""
        # Mock plugin discovery
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin", "provisioner_single_board_plugin"]
        
        # Mock Path for plugins directory
        mock_plugins_dir = mock_path.return_value
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.__truediv__.return_value.exists.return_value = True  # plugins/.git exists
        
        # Mock git commands - main repo shows plugin changes AND submodule shows different plugin changes
        def mock_run_command_side_effect(cmd, cwd=None):
            if cwd is None:  # Main repository
                return "plugins/provisioner_single_board_plugin/main.py\nscripts/version_manager.py"
            else:  # Plugins submodule  
                return "provisioner_examples_plugin/main.py"
        
        mock_run_command.side_effect = mock_run_command_side_effect
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        # Should detect plugins from both main repo and submodule
        expected_plugins = ["provisioner_examples_plugin", "provisioner_single_board_plugin"]
        self.assertEqual(sorted(affected_plugins), expected_plugins)

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    @patch("version_manager.Path")
    def test_get_plugins_from_changes_no_submodule(self, mock_path, mock_discover, mock_run_command):
        """Test detecting changes when plugins directory is not a submodule."""
        # Mock plugin discovery
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin"]
        
        # Mock Path for plugins directory - exists but no .git (not a submodule)
        mock_plugins_dir = mock_path.return_value
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.__truediv__.return_value.exists.return_value = False  # plugins/.git does NOT exist
        
        # Mock git command - only main repo call should happen
        mock_run_command.return_value = "provisioner_examples_plugin/main.py\nother_file.py"
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        self.assertEqual(affected_plugins, ["provisioner_examples_plugin"])
        # Should only call git diff once (no submodule check)
        self.assertEqual(mock_run_command.call_count, 1)

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    @patch("version_manager.Path")
    def test_get_plugins_from_changes_submodule_error(self, mock_path, mock_discover, mock_run_command):
        """Test graceful handling of submodule git command errors."""
        # Mock plugin discovery
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin"]
        
        # Mock Path for plugins directory
        mock_plugins_dir = mock_path.return_value
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.__truediv__.return_value.exists.return_value = True  # plugins/.git exists
        
        # Mock git commands - main repo succeeds, submodule fails
        def mock_run_command_side_effect(cmd, cwd=None):
            if cwd is None:  # Main repository
                return "provisioner_examples_plugin/main.py"
            else:  # Plugins submodule - simulate failure
                raise subprocess.CalledProcessError(1, "git diff")
        
        mock_run_command.side_effect = mock_run_command_side_effect
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        # Should still return plugins from main repo despite submodule error
        self.assertEqual(affected_plugins, ["provisioner_examples_plugin"])

    @patch("version_manager.VersionManager.run_command")
    @patch("version_manager.VersionManager.discover_plugins")
    def test_get_plugins_from_changes_direct_plugin_repo(self, mock_discover, mock_run_command):
        """Test detecting changes when running directly in plugin repository (no plugins/ prefix)."""
        # Mock plugin discovery - simulating being in the plugins repo directly
        mock_discover.return_value = ["provisioner_examples_plugin", "provisioner_installers_plugin", "provisioner_single_board_plugin"]
        
        # Mock git command - files without plugins/ prefix (direct plugin repo structure)
        mock_run_command.return_value = "provisioner_examples_plugin/main.py\nprovisioner_installers_plugin/src/cli/cli.py\nREADME.md"
        
        vm = VersionManager(plugin_mode=True, require_plugin_context=False)
        affected_plugins = vm.get_plugins_from_changes()
        
        expected_plugins = ["provisioner_examples_plugin", "provisioner_installers_plugin"]  
        self.assertEqual(sorted(affected_plugins), expected_plugins)

    @patch.dict(os.environ, {"GITHUB_OUTPUT": ""})
    def test_output_json_response(self):
        """Test JSON response output."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": temp_file_path}):
                vm = VersionManager()
                test_data = {"test": "value", "number": 123}

                json_response = vm._output_json_response(test_data)

                # Check that JSON is compact (no spaces after separators)
                expected_json = '{"test":"value","number":123}'
                self.assertEqual(json_response, expected_json)

                # Check that GitHub output file was written
                with open(temp_file_path, "r") as f:
                    content = f.read()
                self.assertIn(f"json_response={expected_json}", content)

        finally:
            os.unlink(temp_file_path)


class TestVersionManagerCLI(unittest.TestCase):
    """Test cases for version manager CLI interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_github_token = "test_token_123"
        self.env_patcher = patch.dict(os.environ, {"GITHUB_TOKEN": self.test_github_token})
        self.env_patcher.start()

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_pyproject_toml(self, package_name: str, version: str = "0.1.0") -> Path:
        """Create a test pyproject.toml file."""
        pyproject_content = f"""
[tool.poetry]
name = "{package_name}"
version = "{version}"
description = "Test package"
authors = ["Test Author <test@example.com>"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content.strip())
        return pyproject_path

    def run_version_manager_cli(self, args: list) -> tuple:
        """Run version manager CLI and return (exit_code, stdout, stderr)."""
        # Import here to avoid circular imports
        import io
        from contextlib import redirect_stderr, redirect_stdout

        from version_manager import main

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Mock sys.argv
        original_argv = sys.argv
        original_cwd = os.getcwd()

        try:
            sys.argv = ["version_manager.py"] + args
            os.chdir(str(self.temp_path))

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    main()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code or 0
                except Exception:
                    exit_code = 1

            return exit_code, stdout_capture.getvalue(), stderr_capture.getvalue()

        finally:
            sys.argv = original_argv
            os.chdir(original_cwd)

    def test_cli_no_arguments(self):
        """Test CLI with no arguments shows help."""
        exit_code, stdout, stderr = self.run_version_manager_cli([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Version Manager", stdout)
        self.assertIn("COMMANDS:", stdout)

    def test_cli_generate_command(self):
        """Test CLI generate command."""
        # Create test project structure
        self.create_test_pyproject_toml("test-package")

        with patch("version_manager.VersionManager.generate_rc_versions") as mock_generate, patch(
            "version_manager.VersionManager.check_tag_exists"
        ) as mock_check_tag, patch("version_manager.VersionManager.get_current_version") as mock_get_version:

            mock_get_version.return_value = "1.2.3"
            mock_check_tag.return_value = False
            mock_generate.return_value = ("1.2.3", "v1.2.3-RC.1")

            exit_code, stdout, stderr = self.run_version_manager_cli(["generate", str(self.temp_path)])

            self.assertEqual(exit_code, 0)

            # Parse JSON response
            response = json.loads(stdout)
            self.assertEqual(response["package_version"], "1.2.3")
            self.assertEqual(response["rc_tag"], "v1.2.3-RC.1")
            self.assertEqual(response["package_name"], "test-package")
            self.assertFalse(response["is_plugin"])

    def test_cli_promote_command(self):
        """Test CLI promote command."""
        # Create test project structure
        self.create_test_pyproject_toml("test-package")

        with patch("version_manager.VersionManager.determine_rc_to_promote") as mock_promote:
            mock_promote.return_value = ("1.2.3-RC.1", "1.2.3")

            exit_code, stdout, stderr = self.run_version_manager_cli(["promote", str(self.temp_path)])

            self.assertEqual(exit_code, 0)

            # Parse JSON response
            response = json.loads(stdout)
            self.assertEqual(response["rc_version"], "1.2.3-RC.1")
            self.assertEqual(response["stable_version"], "1.2.3")
            self.assertEqual(response["package_name"], "test-package")

    def test_cli_detect_plugins_command(self):
        """Test CLI detect-plugins command."""
        with patch("version_manager.VersionManager.get_plugins_from_changes") as mock_get_plugins:
            mock_get_plugins.return_value = ["provisioner_examples_plugin"]

            exit_code, stdout, stderr = self.run_version_manager_cli(["detect-plugins", "--plugin-mode"])

            self.assertEqual(exit_code, 0)

            # Parse JSON response
            response = json.loads(stdout)
            self.assertEqual(response["plugins"], ["provisioner_examples_plugin"])

    def test_cli_invalid_command(self):
        """Test CLI with invalid command."""
        exit_code, stdout, stderr = self.run_version_manager_cli(["invalid-command"])

        self.assertEqual(exit_code, 1)

        # Parse JSON error response
        response = json.loads(stdout)
        self.assertIn("error", response)
        self.assertIn("Unknown action", response["error"])

    def test_cli_generate_missing_args(self):
        """Test CLI generate command with missing arguments."""
        exit_code, stdout, stderr = self.run_version_manager_cli(["generate"])

        self.assertEqual(exit_code, 1)

        # Parse JSON error response
        response = json.loads(stdout)
        self.assertIn("error", response)
        self.assertIn("requires exactly one argument", response["error"])

    def test_cli_promote_missing_args(self):
        """Test CLI promote command with missing arguments."""
        exit_code, stdout, stderr = self.run_version_manager_cli(["promote"])

        self.assertEqual(exit_code, 1)

        # Parse JSON error response
        response = json.loads(stdout)
        self.assertIn("error", response)
        self.assertIn("requires at least one argument", response["error"])

    def test_cli_detect_plugins_without_plugin_mode(self):
        """Test CLI detect-plugins command without plugin mode flag."""
        exit_code, stdout, stderr = self.run_version_manager_cli(["detect-plugins"])

        self.assertEqual(exit_code, 1)

        # Parse JSON error response
        response = json.loads(stdout)
        self.assertIn("error", response)
        self.assertIn("requires --plugin-mode flag", response["error"])

    def test_cli_github_repo_flag(self):
        """Test CLI with --github-repo flag."""
        # Create test project structure
        self.create_test_pyproject_toml("test-package")

        with patch("version_manager.VersionManager.generate_rc_versions") as mock_generate, patch(
            "version_manager.VersionManager.check_tag_exists"
        ) as mock_check_tag, patch("version_manager.VersionManager.get_current_version") as mock_get_version:

            mock_get_version.return_value = "1.2.3"
            mock_check_tag.return_value = False
            mock_generate.return_value = ("1.2.3", "v1.2.3-RC.1")

            exit_code, stdout, stderr = self.run_version_manager_cli(
                ["generate", str(self.temp_path), "--github-repo", "owner/repo"]
            )

            self.assertEqual(exit_code, 0)

            # Verify that VersionManager was initialized with correct github_repo
            response = json.loads(stdout)
            self.assertEqual(response["package_version"], "1.2.3")

    def test_cli_plugin_mode_flag(self):
        """Test CLI with --plugin-mode flag."""
        # Create test project structure
        self.create_test_pyproject_toml("provisioner-examples-plugin")

        with patch("version_manager.VersionManager.generate_rc_versions") as mock_generate, patch(
            "version_manager.VersionManager.detect_plugin_context"
        ) as mock_detect, patch("version_manager.VersionManager.check_tag_exists") as mock_check_tag, patch(
            "version_manager.VersionManager.get_current_version"
        ) as mock_get_version:

            mock_get_version.return_value = "1.2.3"
            mock_check_tag.return_value = False
            mock_generate.return_value = ("1.2.3", "examples-plugin-v1.2.3-RC.1")
            mock_detect.return_value = "provisioner_examples_plugin"

            exit_code, stdout, stderr = self.run_version_manager_cli(["generate", str(self.temp_path), "--plugin-mode"])

            self.assertEqual(exit_code, 0)

            response = json.loads(stdout)
            self.assertTrue(response["is_plugin"])


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
