#!/usr/bin/env python3
"""
Version Manager Script

This script handles version management for both RC creation and GA promotion.
It encapsulates all RC-related behavior and version validation logic.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tomllib

RC_VERSION_SUFFIX = "RC"


@dataclass
class CliArguments:
    """Container for parsed CLI arguments."""

    action: str
    project_folder_path: Optional[str] = None
    rc_version: Optional[str] = None
    plugin_mode: bool = False
    github_repo: Optional[str] = None


@dataclass
class CommandResponse:
    """Container for command response data."""

    data: Dict
    success: bool = True
    error_message: Optional[str] = None


class VersionManager:
    """Manages version calculations and RC validation for release workflows."""

    def __init__(
        self,
        plugin_mode: bool = False,
        require_plugin_context: bool = True,
        github_repo: Optional[str] = None,
        project_path_hint: Optional[str] = None,
    ):
        """
        Initialize VersionManager.

        Args:
            plugin_mode: Enable plugin-specific behavior
            require_plugin_context: Require plugin context when in plugin mode
            github_repo: GitHub repository in format "owner/repo"
            project_path_hint: Path hint for plugin detection
        """
        self._validate_github_token()

        self.plugin_mode = plugin_mode
        self.github_repo = github_repo
        self.package_name = None

        self.plugin_name = self._initialize_plugin_context(plugin_mode, require_plugin_context, project_path_hint)

    def _validate_github_token(self) -> None:
        """Validate that GITHUB_TOKEN environment variable is set."""
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

    def _initialize_plugin_context(
        self, plugin_mode: bool, require_plugin_context: bool, project_path_hint: Optional[str]
    ) -> Optional[str]:
        """Initialize plugin context if needed."""
        if not plugin_mode:
            return None

        plugin_name = self.detect_plugin_context(project_path_hint)

        if require_plugin_context and not plugin_name:
            raise ValueError("Plugin mode enabled but no plugin detected in current context")

        return plugin_name

    def output_json_response(self, data: dict) -> str:
        """
        Output structured JSON response and set GitHub Actions outputs.

        Args:
            data: Dictionary containing the response data

        Returns:
            JSON string of the response
        """
        json_response = json.dumps(data, separators=(",", ":"))

        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as file:
                file.write(f"json_response={json_response}\n")

        return json_response

    def validate_project_path(self, project_path: str) -> str:
        """
        Validate that the project path contains a valid pyproject.toml file.

        Args:
            project_path: Path to the project directory

        Returns:
            Package name from pyproject.toml

        Raises:
            ValueError: If pyproject.toml is missing or invalid
        """
        project_dir = Path(project_path)
        self._validate_project_directory(project_dir)

        pyproject_path = project_dir / "pyproject.toml"
        if not pyproject_path.exists():
            raise ValueError(f"Project path does not contain pyproject.toml: {project_path}")

        package_name = self._extract_package_name_from_pyproject(pyproject_path, project_path)
        self.package_name = package_name
        return package_name

    def _validate_project_directory(self, project_dir: Path) -> None:
        """Validate that project directory exists and is a directory."""
        if not project_dir.exists():
            raise ValueError(f"Project path does not exist: {project_dir}")

        if not project_dir.is_dir():
            raise ValueError(f"Project path is not a directory: {project_dir}")

    def _extract_package_name_from_pyproject(self, pyproject_path: Path, project_path: str) -> str:
        """Extract package name from pyproject.toml file."""
        try:
            with open(pyproject_path, "rb") as file:
                pyproject_data = tomllib.load(file)
        except Exception as e:
            raise ValueError(f"Failed to parse pyproject.toml in {project_path}: {str(e)}")

        return self._get_package_name_from_toml_data(pyproject_data, project_path)

    def _get_package_name_from_toml_data(self, pyproject_data: dict, project_path: str) -> str:
        """Extract package name from parsed TOML data."""
        if "tool" not in pyproject_data:
            raise ValueError(f"pyproject.toml in {project_path} does not contain [tool] section")

        if "poetry" not in pyproject_data["tool"]:
            raise ValueError(f"pyproject.toml in {project_path} does not contain [tool.poetry] section")

        if "name" not in pyproject_data["tool"]["poetry"]:
            raise ValueError(
                f"pyproject.toml in {project_path} does not contain 'name' attribute in [tool.poetry] section"
            )

        package_name = pyproject_data["tool"]["poetry"]["name"]
        if not package_name or not isinstance(package_name, str):
            raise ValueError(f"Invalid package name in pyproject.toml: {package_name}")

        return package_name

    def discover_plugins(self) -> List[str]:
        """Dynamically discover plugin folders by scanning the plugins directory."""
        plugins_dir = self._find_plugins_directory()
        if not plugins_dir:
            return []

        return self._scan_plugin_directories(plugins_dir)

    def _find_plugins_directory(self) -> Optional[Path]:
        """Find the plugins directory based on current working directory."""
        cwd = Path.cwd()

        # Check if we're already in plugins directory
        if cwd.name == "plugins":
            return cwd

        # Check if plugins directory exists in current directory
        if (cwd / "plugins").exists():
            return cwd / "plugins"

        # Check if we're in a subdirectory of plugins
        if "plugins" in cwd.parts:
            for i, part in enumerate(cwd.parts):
                if part == "plugins":
                    return Path("/".join(cwd.parts[: i + 1]))

        return None

    def _scan_plugin_directories(self, plugins_dir: Path) -> List[str]:
        """Scan for valid plugin directories."""
        plugin_names = []

        for item in plugins_dir.iterdir():
            if self._is_valid_plugin_directory(item):
                plugin_names.append(item.name)

        plugin_names.sort()
        return plugin_names

    def _is_valid_plugin_directory(self, directory: Path) -> bool:
        """Check if a directory is a valid plugin directory."""
        return (
            directory.is_dir()
            and re.match(r"^provisioner_.*_plugin$", directory.name)
            and (directory / "pyproject.toml").exists()
        )

    def run_command(self, cmd: str, cwd: Path = None) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(cmd, shell=True, cwd=cwd or Path.cwd(), capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Command failed: {cmd}. Error: {e.stderr}")

    def detect_plugin_context(self, project_path: Optional[str] = None) -> Optional[str]:
        """Detect if running in plugin context and return plugin name."""
        plugin_names = self.discover_plugins()

        # Try to detect from project_path first
        if project_path:
            plugin_from_path = self._detect_plugin_from_path(project_path, plugin_names)
            if plugin_from_path:
                return plugin_from_path

        # Try to detect from current working directory
        return self._detect_plugin_from_cwd(plugin_names)

    def _detect_plugin_from_path(self, project_path: str, plugin_names: List[str]) -> Optional[str]:
        """Detect plugin name from project path."""
        project_path_obj = Path(project_path)

        # Handle explicit paths like "plugins/provisioner_examples_plugin"
        if project_path_obj.parts and project_path_obj.parts[0] == "plugins" and len(project_path_obj.parts) >= 2:
            potential_plugin = project_path_obj.parts[1]
            if potential_plugin in plugin_names:
                return potential_plugin

        # Check if the project path contains a plugin name
        for plugin in plugin_names:
            if plugin in str(project_path_obj) or project_path_obj.name == plugin:
                return plugin

        return None

    def _detect_plugin_from_cwd(self, plugin_names: List[str]) -> Optional[str]:
        """Detect plugin name from current working directory."""
        cwd = Path.cwd()

        # Check if we're in plugins submodule directory
        if "plugins" in cwd.parts:
            for plugin in plugin_names:
                if plugin in str(cwd):
                    return plugin

        # Check if current directory is a plugin directory
        for plugin in plugin_names:
            if cwd.name == plugin or plugin in str(cwd):
                return plugin

        return None

    def get_plugins_from_changes(self, project_folder_path: str) -> List[str]:
        """Analyze changed files to identify affected plugins in the specified directory."""
        try:
            return self._analyze_git_changes(project_folder_path)
        except Exception:
            return []

    def _analyze_git_changes(self, project_folder_path: str) -> List[str]:
        """Analyze git changes to find affected plugins."""
        project_dir = Path(project_folder_path)

        changed_files = self.run_command("git diff --name-only HEAD~1", cwd=project_dir)
        if not changed_files.strip():
            return []

        plugin_names = self._get_plugin_names_for_directory(project_dir)
        changed_file_list = [f.strip() for f in changed_files.split("\n") if f.strip()]

        return self._find_affected_plugins(changed_file_list, plugin_names)

    def _get_plugin_names_for_directory(self, project_dir: Path) -> List[str]:
        """Get plugin names relative to the specified directory."""
        original_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            return self.discover_plugins()
        finally:
            os.chdir(original_cwd)

    def _find_affected_plugins(self, changed_files: List[str], plugin_names: List[str]) -> List[str]:
        """Find which plugins are affected by the changed files."""
        affected_plugins = []

        for changed_file in changed_files:
            for plugin in plugin_names:
                if changed_file.startswith(f"{plugin}/"):
                    if plugin not in affected_plugins:
                        affected_plugins.append(plugin)
                    break

        return affected_plugins

    def get_tag_name(self, version: str) -> str:
        """Generate the appropriate tag name based on context (plugin vs main project)."""
        if self.plugin_mode and self.plugin_name:
            return self._generate_plugin_tag_name(version)
        else:
            return f"v{version}"

    def _generate_plugin_tag_name(self, version: str) -> str:
        """Generate tag name for plugin."""
        plugin_core_name = self._extract_plugin_core_name(self.plugin_name)
        plugin_tag_name = plugin_core_name.replace("_", "-") + "-plugin"
        return f"{plugin_tag_name}-v{version}"

    def _extract_plugin_core_name(self, plugin_name: str) -> str:
        """Extract core name from plugin name."""
        core_name = plugin_name

        if core_name.startswith("provisioner_"):
            core_name = core_name[len("provisioner_") :]

        if core_name.endswith("_plugin"):
            core_name = core_name[: -len("_plugin")]

        return core_name

    def get_package_name(self) -> str:
        """Get the package name for PyPI based on context."""
        if self.package_name:
            return self.package_name

        # Fallback to legacy behavior for backward compatibility
        if self.plugin_mode and self.plugin_name:
            return self.plugin_name.replace("_", "-")
        else:
            return "provisioner"

    def get_current_version(self, project_dir: Path) -> str:
        """Get current version from poetry."""
        output = self.run_command("poetry version", cwd=project_dir)
        # Extract version from "package-name x.y.z" format
        version = output.split()[-1]
        return version.strip()

    def check_tag_exists(self, version: str) -> bool:
        """Check if a git tag exists for the given version using GitHub CLI."""
        tag_name = self.get_tag_name(version)

        try:
            return self._check_tag_exists_remote(tag_name) or self._check_tag_exists_local(tag_name)
        except Exception:
            return self._check_tag_exists_local_fallback(tag_name)

    def _check_tag_exists_remote(self, tag_name: str) -> bool:
        """Check if tag exists in remote repository."""
        repo_path = self.github_repo if self.github_repo else ":owner/:repo"
        tags_output = self.run_command(f"gh api repos/{repo_path}/tags --paginate --jq '.[].name'")
        remote_tags = tags_output.split("\n") if tags_output else []
        return tag_name in remote_tags

    def _check_tag_exists_local(self, tag_name: str) -> bool:
        """Check if tag exists in local repository."""
        local_tags = self.run_command("git tag -l")
        return tag_name in local_tags.split("\n")

    def _check_tag_exists_local_fallback(self, tag_name: str) -> bool:
        """Fallback method to check local tags when remote check fails."""
        try:
            tags = self.run_command("git tag -l")
            return tag_name in tags.split("\n")
        except Exception:
            return False

    def check_release_exists(self, version: str) -> Tuple[bool, bool]:
        """
        Check if a GitHub release exists and if it's a pre-release.

        Returns:
            Tuple[bool, bool]: (exists, is_prerelease)
        """
        tag_name = self.get_tag_name(version)

        try:
            repo_flag = f"--repo {self.github_repo}" if self.github_repo else ""
            result = self.run_command(f'gh release view "{tag_name}" --json isPrerelease {repo_flag}')
            release_data = json.loads(result)
            return True, release_data.get("isPrerelease", False)
        except Exception:
            return False, False

    def validate_rc_version_format(self, rc_version: str) -> bool:
        """Validate RC version format (x.y.z-RC.N)."""
        pattern = r"^\d+\.\d+\.\d+-RC\.\d+$"
        return bool(re.match(pattern, rc_version))

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into major, minor, patch components."""
        clean_version = re.sub(rf"-{RC_VERSION_SUFFIX}\.\d+$", "", version)
        parts = clean_version.split(".")

        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version numbers in: {version}")

    def get_latest_rc_version(self) -> Optional[str]:
        """Get the latest RC version from GitHub releases."""
        rc_pattern, tag_prefix_len = self._build_rc_pattern()

        # Try GitHub API first, then fall back to local git tags
        try:
            rc_tags = self._get_rc_tags_from_github(rc_pattern)
            if rc_tags:
                return self._get_latest_version_from_tags(rc_tags, tag_prefix_len)
        except Exception:
            pass

        # Fallback: check local git tags
        try:
            rc_tags = self._get_rc_tags_from_local(rc_pattern)
            if rc_tags:
                return self._get_latest_version_from_tags(rc_tags, tag_prefix_len)
        except Exception:
            pass

        return None

    def _build_rc_pattern(self) -> Tuple[str, int]:
        """Build RC pattern and tag prefix length based on context."""
        if self.plugin_mode and self.plugin_name:
            plugin_core_name = self._extract_plugin_core_name(self.plugin_name)
            plugin_tag_name = plugin_core_name.replace("_", "-") + "-plugin"
            rc_pattern = rf"^{re.escape(plugin_tag_name)}-v\d+\.\d+\.\d+-RC\.\d+$"
            tag_prefix_len = len(f"{plugin_tag_name}-v")
        else:
            rc_pattern = r"^v\d+\.\d+\.\d+-RC\.\d+$"
            tag_prefix_len = 1

        return rc_pattern, tag_prefix_len

    def _get_rc_tags_from_github(self, rc_pattern: str) -> List[str]:
        """Get RC tags from GitHub API."""
        repo_path = self.github_repo if self.github_repo else ":owner/:repo"
        tags_output = self.run_command(f"gh api repos/{repo_path}/tags --paginate --jq '.[].name'")

        if tags_output:
            return [tag for tag in tags_output.split("\n") if re.match(rc_pattern, tag)]
        return []

    def _get_rc_tags_from_local(self, rc_pattern: str) -> List[str]:
        """Get RC tags from local git repository."""
        cwd = Path("plugins") if self.plugin_mode and Path("plugins").exists() else None
        local_tags_output = self.run_command("git tag -l", cwd=cwd)

        if local_tags_output:
            return [tag for tag in local_tags_output.split("\n") if re.match(rc_pattern, tag)]
        return []

    def _get_latest_version_from_tags(self, rc_tags: List[str], tag_prefix_len: int) -> Optional[str]:
        """Get the latest version from a list of RC tags."""
        if not rc_tags:
            return None

        # Sort by version (extract version numbers for sorting)
        rc_tags.sort(key=lambda x: [int(i) for i in re.findall(r"\d+", x)], reverse=True)
        return rc_tags[0][tag_prefix_len:]

    def generate_rc_versions(self, project_folder_path: str) -> Tuple[str, str]:
        """
        Generate both the package version (final) and RC tag (for git) following
        'build once, promote many' principle.

        Returns:
            Tuple[str, str]: (package_version, rc_tag)
        """
        project_dir = Path(project_folder_path)
        current_version = self.get_current_version(project_dir)

        return self._calculate_rc_versions(current_version)

    def _calculate_rc_versions(self, current_version: str) -> Tuple[str, str]:
        """Calculate RC versions based on current version."""
        rc_pattern = rf"-{RC_VERSION_SUFFIX}\.(\d+)$"
        rc_match = re.search(rc_pattern, current_version)

        if rc_match:
            return self._handle_existing_rc_version(current_version, rc_match)
        else:
            return self._handle_new_rc_version(current_version)

    def _handle_existing_rc_version(self, current_version: str, rc_match) -> Tuple[str, str]:
        """Handle case where current version is already an RC."""
        package_version = re.sub(rf"-{RC_VERSION_SUFFIX}\.(\d+)$", "", current_version)
        base_version = package_version
        rc_number = int(rc_match.group(1))

        # Find the next available RC number
        while True:
            next_rc_number = rc_number + 1
            candidate_rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.{next_rc_number}"
            if not self.check_tag_exists(candidate_rc_version):
                rc_tag = self.get_tag_name(candidate_rc_version)
                return package_version, rc_tag
            rc_number = next_rc_number

    def _handle_new_rc_version(self, current_version: str) -> Tuple[str, str]:
        """Handle case where current version is not an RC."""
        if self.check_tag_exists(current_version):
            # Version exists as tag, increment patch for next version
            major, minor, patch = self.parse_version(current_version)
            package_version = f"{major}.{minor}.{patch + 1}"
        else:
            # Use current version as package version
            package_version = current_version

        # Find the first available RC number for this base version
        rc_number = 1
        while True:
            candidate_rc_version = f"{package_version}-{RC_VERSION_SUFFIX}.{rc_number}"
            if not self.check_tag_exists(candidate_rc_version):
                rc_tag = self.get_tag_name(candidate_rc_version)
                return package_version, rc_tag
            rc_number += 1

    def determine_rc_to_promote(self, input_rc_version: Optional[str] = None) -> Tuple[str, str]:
        """
        Determine which RC version to promote to GA.

        Args:
            input_rc_version: Optional RC version provided by user

        Returns:
            Tuple[str, str]: (rc_version, stable_version)
        """
        if input_rc_version and input_rc_version.strip():
            rc_version = self._validate_and_get_provided_rc(input_rc_version.strip())
        else:
            rc_version = self._get_latest_rc_for_promotion()

        stable_version = re.sub(rf"-{RC_VERSION_SUFFIX}\.\d+$", "", rc_version)
        return rc_version, stable_version

    def _validate_and_get_provided_rc(self, input_rc_version: str) -> str:
        """Validate and return provided RC version."""
        if not self.validate_rc_version_format(input_rc_version):
            raise ValueError(f"Invalid RC version format: {input_rc_version}. Expected format: x.y.z-RC.N")

        exists, is_prerelease = self.check_release_exists(input_rc_version)
        if not exists:
            raise ValueError(f"RC version v{input_rc_version} not found in GitHub releases")

        if not is_prerelease:
            raise ValueError(f"Release v{input_rc_version} is not marked as pre-release")

        return input_rc_version

    def _get_latest_rc_for_promotion(self) -> str:
        """Get the latest RC version for promotion."""
        rc_version = self.get_latest_rc_version()
        if not rc_version:
            raise ValueError("No RC versions found in GitHub releases")
        return rc_version


class VersionManagerCLI:
    """Handles CLI operations for VersionManager."""

    def __init__(self):
        self.version_manager = None

    def run(self) -> None:
        """Main entry point for CLI execution."""
        try:
            args = self._parse_command_line_arguments()
            self.version_manager = self._create_version_manager(args)
            response = self._execute_command(args)
            self._output_response(response)
        except Exception as e:
            self._handle_error(e)

    def _parse_command_line_arguments(self) -> CliArguments:
        """Parse and validate command line arguments."""
        if len(sys.argv) < 2:
            print_help()
            sys.exit(1)

        # Parse action
        action = sys.argv[1]

        # Parse flags
        plugin_mode = self._extract_flag("--plugin-mode")
        github_repo = self._extract_flag_with_value("--github-repo")

        # Parse positional arguments based on action
        project_folder_path, rc_version = self._parse_positional_arguments(action)

        return CliArguments(
            action=action,
            project_folder_path=project_folder_path,
            rc_version=rc_version,
            plugin_mode=plugin_mode,
            github_repo=github_repo,
        )

    def _extract_flag(self, flag_name: str) -> bool:
        """Extract and remove a boolean flag from sys.argv."""
        if flag_name in sys.argv:
            sys.argv.remove(flag_name)
            return True
        return False

    def _extract_flag_with_value(self, flag_name: str) -> Optional[str]:
        """Extract and remove a flag with value from sys.argv."""
        for i, arg in enumerate(sys.argv):
            if arg == flag_name and i + 1 < len(sys.argv):
                value = sys.argv[i + 1]
                # Remove both flag and value
                sys.argv.pop(i + 1)
                sys.argv.pop(i)
                return value
        return None

    def _parse_positional_arguments(self, action: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse positional arguments based on action."""
        if action == "generate":
            if len(sys.argv) != 3:
                raise ValueError("generate command requires exactly one argument: <project_folder_path>")
            return sys.argv[2], None

        elif action == "promote":
            if len(sys.argv) < 3:
                raise ValueError("promote command requires at least one argument: <project_folder_path> [rc_version]")
            project_folder_path = sys.argv[2]
            rc_version = sys.argv[3] if len(sys.argv) > 3 else None
            return project_folder_path, rc_version

        elif action == "detect-plugins":
            if len(sys.argv) != 3:
                raise ValueError("detect-plugins command requires exactly one argument: <project_folder_path>")
            return sys.argv[2], None

        else:
            return None, None

    def _create_version_manager(self, args: CliArguments) -> VersionManager:
        """Create VersionManager instance with appropriate configuration."""
        require_context = args.action != "detect-plugins"
        project_path_hint = args.project_folder_path

        return VersionManager(
            plugin_mode=args.plugin_mode,
            require_plugin_context=require_context,
            github_repo=args.github_repo,
            project_path_hint=project_path_hint,
        )

    def _execute_command(self, args: CliArguments) -> CommandResponse:
        """Execute the specified command and return response."""
        command_handlers = {
            "generate": self._handle_generate_command,
            "promote": self._handle_promote_command,
            "detect-plugins": self._handle_detect_plugins_command,
        }

        handler = command_handlers.get(args.action)
        if not handler:
            return self._create_unknown_action_response(args.action)

        return handler(args)

    def _handle_generate_command(self, args: CliArguments) -> CommandResponse:
        """Handle the generate command."""
        try:
            self.version_manager.validate_project_path(args.project_folder_path)
            package_version, rc_tag = self.version_manager.generate_rc_versions(args.project_folder_path)

            response_data = {
                "package_version": package_version,
                "rc_tag": rc_tag,
                "plugin_name": self.version_manager.plugin_name or "",
                "package_name": self.version_manager.get_package_name(),
                "project_folder_path": args.project_folder_path,
                "is_plugin": args.plugin_mode,
            }

            return CommandResponse(data=response_data)

        except ValueError as e:
            return CommandResponse(
                data={
                    "error": str(e),
                    "action": "generate",
                    "project_path": args.project_folder_path,
                    "requirement": "Project path must contain a valid pyproject.toml with [tool.poetry] section and 'name' attribute",
                },
                success=False,
            )

    def _handle_promote_command(self, args: CliArguments) -> CommandResponse:
        """Handle the promote command."""
        try:
            self.version_manager.validate_project_path(args.project_folder_path)
            rc_version, stable_version = self.version_manager.determine_rc_to_promote(args.rc_version)

            response_data = {
                "rc_version": rc_version,
                "stable_version": stable_version,
                "plugin_name": self.version_manager.plugin_name or "",
                "package_name": self.version_manager.get_package_name(),
                "is_plugin": args.plugin_mode,
                "input_rc_version": args.rc_version or "auto-detected",
                "project_folder_path": args.project_folder_path,
            }

            return CommandResponse(data=response_data)

        except ValueError as e:
            return CommandResponse(
                data={
                    "error": str(e),
                    "action": "promote",
                    "project_path": args.project_folder_path,
                    "requirement": "Project path must contain a valid pyproject.toml with [tool.poetry] section and 'name' attribute",
                },
                success=False,
            )

    def _handle_detect_plugins_command(self, args: CliArguments) -> CommandResponse:
        """Handle the detect-plugins command."""
        if not args.plugin_mode:
            return CommandResponse(
                data={
                    "error": "detect-plugins command requires --plugin-mode flag",
                    "usage": "python version_manager.py detect-plugins <project_folder_path> --plugin-mode [--github-repo <owner/repo>]",
                    "purpose": "Analyze git changes to identify modified plugins for CI matrix",
                },
                success=False,
            )

        affected_plugins = self.version_manager.get_plugins_from_changes(args.project_folder_path)
        response_data = {"plugins": affected_plugins, "repository": self.version_manager.github_repo or "local"}

        return CommandResponse(data=response_data)

    def _create_unknown_action_response(self, action: str) -> CommandResponse:
        """Create response for unknown action."""
        return CommandResponse(
            data={
                "error": f"Unknown action '{action}'",
                "available_actions": [
                    {"name": "generate", "description": "Calculate RC versions for release candidate creation"},
                    {"name": "promote", "description": "Promote existing RC to General Availability"},
                    {"name": "detect-plugins", "description": "Detect changed plugins for CI matrix workflows"},
                ],
                "help": "Use 'python version_manager.py' without arguments for full help.",
            },
            success=False,
        )

    def _output_response(self, response: CommandResponse) -> None:
        """Output the command response."""
        json_response = self.version_manager.output_json_response(response.data)
        print(json_response)

        if not response.success:
            sys.exit(1)

    def _handle_error(self, error: Exception) -> None:
        """Handle unexpected errors."""
        if isinstance(error, ValueError) and "argument" in str(error):
            # Handle argument parsing errors
            error_data = {"error": str(error)}
        else:
            # Handle unexpected errors
            error_data = {"error": str(error), "action": "unknown"}

        # Create a minimal version manager for output if needed
        if not self.version_manager:
            try:
                self.version_manager = VersionManager(require_plugin_context=False)
            except Exception:
                # If we can't create version manager, output JSON directly
                print(json.dumps(error_data, separators=(",", ":")))
                sys.exit(1)

        json_response = self.version_manager.output_json_response(error_data)
        print(json_response)
        sys.exit(1)


def print_help():
    """Print comprehensive help information for all commands."""
    print("Version Manager - Handles RC creation and GA promotion for main project and plugins")
    print()
    print("OUTPUT FORMAT:")
    print("  ALL commands return ONLY structured JSON responses via stdout")
    print("  Complete JSON response is automatically set as 'json_response' GITHUB_OUTPUT variable")
    print()
    print("COMMANDS:")
    print()
    print("  generate <project_folder_path> [--plugin-mode] [--github-repo <owner/repo>]")
    print("    Purpose: Calculate and generate RC versions for creating release candidates")
    print("    Usage:   Used during CI to create new RC releases")
    print("    Action:  READ-ONLY - No changes to remote repositories, only calculates version data")
    print(
        "    Requirements: Project path must contain a valid pyproject.toml with [tool.poetry] section and 'name' attribute"
    )
    print("    JSON Response Fields:")
    print("             - package_version: Final version for packages (e.g., '1.2.3')")
    print("             - rc_tag: RC git tag (e.g., '1.2.3-RC.1')")
    print("             - plugin_name: Plugin name if in plugin mode (empty string if not plugin)")
    print("             - package_name: PyPI package name (read from pyproject.toml)")
    print("             - project_folder_path: Project path that was processed")
    print("             - is_plugin: Boolean indicating if this is a plugin")
    print("    Example: python version_manager.py generate provisioner --github-repo ZachiNachshon/provisioner")
    print(
        "             python version_manager.py generate plugins/provisioner_examples_plugin --plugin-mode --github-repo ZachiNachshon/provisioner-plugins"
    )
    print()
    print("  promote <project_folder_path> [rc_version] [--plugin-mode] [--github-repo <owner/repo>]")
    print("    Purpose: Promote an existing RC to General Availability (GA/stable)")
    print("    Usage:   Used during GA promotion workflows to convert RC to stable")
    print("    Action:  READ-ONLY - No changes to remote repositories, only calculates promotion data")
    print("    Inputs:  project_folder_path - path to project directory")
    print("             rc_version (optional) - specific RC to promote (auto-detects latest if omitted)")
    print("    JSON Response Fields:")
    print("             - rc_version: RC version being promoted (e.g., '1.2.3-RC.1')")
    print("             - stable_version: Final stable version (e.g., '1.2.3')")
    print("             - plugin_name: Plugin name if in plugin mode (empty string if not plugin)")
    print("             - package_name: PyPI package name")
    print("             - is_plugin: Boolean indicating if this is a plugin")
    print("             - input_rc_version: Input RC version or 'auto-detected'")
    print("    Example: python version_manager.py promote provisioner --github-repo ZachiNachshon/provisioner")
    print(
        "             python version_manager.py promote plugins/provisioner_examples_plugin 1.2.3-RC.1 --plugin-mode --github-repo ZachiNachshon/provisioner-plugins"
    )
    print()
    print("  detect-plugins <project_folder_path> --plugin-mode [--github-repo <owner/repo>]")
    print("    Purpose: Analyze git changes to identify which plugins have been modified in the specified directory")
    print("    Usage:   Used in CI matrix workflows to determine which plugins need RC creation")
    print("    Action:  READ-ONLY - No changes to remote repositories, only analyzes local git changes")
    print("    Inputs:  project_folder_path - path to directory containing plugins (e.g., 'plugins' or '.')")
    print("    JSON Response Fields:")
    print(
        '             - plugins: Array of changed plugin names (e.g., ["provisioner_examples_plugin"] or [] if no changes)'
    )
    print("             - repository: Repository being analyzed")
    print(
        "    Example: python version_manager.py detect-plugins plugins --plugin-mode --github-repo ZachiNachshon/provisioner-plugins"
    )
    print(
        "             python version_manager.py detect-plugins . --plugin-mode  # When running directly in plugins repo"
    )
    print()
    print("FLAGS:")
    print("  --plugin-mode               Enable plugin-specific behavior (required for plugin operations)")
    print(
        "  --github-repo <owner/repo>  Specify GitHub repository for version queries (e.g., 'ZachiNachshon/provisioner-plugins')"
    )
    print("                              Required when querying different repositories for RC versions")
    print()
    print("GITHUB ACTIONS INTEGRATION:")
    print("  - All commands output ONLY valid JSON to stdout")
    print("  - Complete JSON response is automatically set as 'json_response' GITHUB_OUTPUT variable")
    print("  - Use 'fromJSON(steps.<step_id>.outputs.json_response)' in workflows to access individual fields")
    print("  - Error responses are also structured JSON with error details")
    print()
    print("SAMPLE JSON RESPONSES:")
    print(
        '  Generate: {"package_version":"1.2.3","rc_tag":"1.2.3-RC.1","plugin_name":"","package_name":"provisioner","project_folder_path":"provisioner","is_plugin":false}'
    )
    print(
        '  Promote:  {"rc_version":"1.2.3-RC.1","stable_version":"1.2.3","plugin_name":"","package_name":"provisioner","is_plugin":false,"input_rc_version":"auto-detected"}'
    )
    print('  Detect:   {"plugins":["provisioner_examples_plugin"],"repository":"local"}')
    print('  Error:    {"error":"Invalid RC version format","action":"promote"}')
    print()
    print("REPOSITORY TARGETING:")
    print("  Main project: Use --github-repo ZachiNachshon/provisioner")
    print("  Plugins:      Use --github-repo ZachiNachshon/provisioner-plugins")


def main():
    """Main function that handles CLI execution."""
    cli = VersionManagerCLI()
    cli.run()


if __name__ == "__main__":
    main()
