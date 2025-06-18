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
from pathlib import Path
from typing import List, Optional, Tuple

import tomllib

RC_VERSION_SUFFIX = "RC"


class VersionManager:
    """Manages version calculations and RC validation for release workflows."""

    def __init__(
        self,
        plugin_mode: bool = False,
        require_plugin_context: bool = True,
        github_repo: Optional[str] = None,
        project_path_hint: Optional[str] = None,
    ):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.plugin_mode = plugin_mode
        self.plugin_name = self.detect_plugin_context(project_path_hint) if plugin_mode else None
        self.github_repo = github_repo  # Format: "owner/repo" (e.g., "ZachiNachshon/provisioner-plugins")
        self.package_name = None  # Will be set when validating project path

        if plugin_mode and require_plugin_context and not self.plugin_name:
            raise ValueError("Plugin mode enabled but no plugin detected in current context")

    def _output_json_response(self, data: dict) -> str:
        """
        Output structured JSON response and set GitHub Actions outputs.

        Args:
            data: Dictionary containing the response data

        Returns:
            JSON string of the response
        """
        # Output compact JSON without indentation for GitHub Actions compatibility
        json_response = json.dumps(data, separators=(",", ":"))

        # Set GitHub Action outputs - ONLY the JSON string
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                # Set the compact JSON response (no newlines to escape)
                f.write(f"json_response={json_response}\n")

        return json_response

    def validate_project_path(self, project_path: str) -> str:
        """
        Validate that the project path contains a pyproject.toml file and read the package name.

        Args:
            project_path: Path to the project directory

        Returns:
            str: Package name from pyproject.toml

        Raises:
            ValueError: If pyproject.toml is missing or invalid
        """
        project_dir = Path(project_path)

        if not project_dir.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        if not project_dir.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        pyproject_path = project_dir / "pyproject.toml"
        if not pyproject_path.exists():
            raise ValueError(f"Project path does not contain pyproject.toml: {project_path}")

        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse pyproject.toml in {project_path}: {str(e)}")

        # Extract package name from [tool.poetry] section
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

        # Store the package name for later use
        self.package_name = package_name
        return package_name

    def discover_plugins(self) -> List[str]:
        """Dynamically discover plugin folders by scanning the plugins directory."""
        plugin_names = []

        # Try to find plugins directory relative to current working directory
        plugins_dir = None
        cwd = Path.cwd()

        # Check if we're already in plugins directory
        if cwd.name == "plugins":
            plugins_dir = cwd
        # Check if plugins directory exists in current directory
        elif (cwd / "plugins").exists():
            plugins_dir = cwd / "plugins"
        # Check if we're in a subdirectory of plugins
        elif "plugins" in cwd.parts:
            # Find the plugins directory in the path
            for i, part in enumerate(cwd.parts):
                if part == "plugins":
                    plugins_dir = Path("/".join(cwd.parts[: i + 1]))
                    break

        if not plugins_dir or not plugins_dir.exists():
            return []

        # Scan for directories matching provisioner_*_plugin pattern
        for item in plugins_dir.iterdir():
            if item.is_dir() and re.match(r"^provisioner_.*_plugin$", item.name) and (item / "pyproject.toml").exists():
                plugin_names.append(item.name)

        plugin_names.sort()  # Sort for consistent ordering
        return plugin_names

    def run_command(self, cmd: str, cwd: Path = None) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(cmd, shell=True, cwd=cwd or Path.cwd(), capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Command failed: {cmd}. Error: {e.stderr}")

    def detect_plugin_context(self, project_path: Optional[str] = None) -> Optional[str]:
        """Detect if running in plugin context and return plugin name."""
        cwd = Path.cwd()
        plugin_names = self.discover_plugins()

        # If project_path is provided, try to extract plugin name from it
        if project_path:
            project_path_obj = Path(project_path)

            # Handle explicit paths like "plugins/provisioner_examples_plugin"
            if project_path_obj.parts and project_path_obj.parts[0] == "plugins" and len(project_path_obj.parts) >= 2:
                potential_plugin = project_path_obj.parts[1]
                if potential_plugin in plugin_names:
                    return potential_plugin

            # Check if the project path contains a plugin name (legacy behavior)
            for plugin in plugin_names:
                if plugin in str(project_path_obj) or project_path_obj.name == plugin:
                    return plugin

        # Check if we're in plugins submodule directory
        if "plugins" in cwd.parts:
            for plugin in plugin_names:
                if plugin in str(cwd):
                    return plugin

        # Check if a specific plugin directory was passed as project_folder_path
        for plugin in plugin_names:
            if cwd.name == plugin or plugin in str(cwd):
                return plugin

        return None

    def get_plugins_from_changes(self) -> List[str]:
        """Analyze changed files to identify affected plugins."""
        try:
            changed_files = self.run_command("git diff --name-only HEAD~1")
            affected_plugins = []
            plugin_names = self.discover_plugins()

            for line in changed_files.split("\n"):
                if not line.strip():
                    continue

                for plugin in plugin_names:
                    if line.startswith(plugin + "/"):
                        if plugin not in affected_plugins:
                            affected_plugins.append(plugin)

            return affected_plugins
        except Exception:
            return []

    def _get_tag_name(self, version: str) -> str:
        """Generate the appropriate tag name based on context (plugin vs main project)."""
        if self.plugin_mode and self.plugin_name:
            # Convert plugin name to tag format: provisioner_examples_plugin -> examples-plugin
            # Remove "provisioner_" prefix and "_plugin" suffix, then add "-plugin"
            plugin_core_name = self.plugin_name
            if plugin_core_name.startswith("provisioner_"):
                plugin_core_name = plugin_core_name[len("provisioner_") :]
            if plugin_core_name.endswith("_plugin"):
                plugin_core_name = plugin_core_name[: -len("_plugin")]

            plugin_tag_name = plugin_core_name.replace("_", "-") + "-plugin"
            return f"{plugin_tag_name}-v{version}"
        else:
            return f"v{version}"

    def _get_package_name(self) -> str:
        """Get the package name for PyPI based on context."""
        # If package name was read from pyproject.toml, use that
        if self.package_name:
            return self.package_name

        # Fallback to legacy behavior for backward compatibility
        if self.plugin_mode and self.plugin_name:
            return self.plugin_name.replace("_", "-")
        else:
            return "provisioner"  # Main project package name

    def get_current_version(self, project_dir: Path) -> str:
        """Get current version from poetry."""
        output = self.run_command("poetry version", cwd=project_dir)
        # Extract version from "package-name x.y.z" format
        version = output.split()[-1]
        return version.strip()

    def check_tag_exists(self, version: str) -> bool:
        """Check if a git tag exists for the given version using GitHub CLI."""
        # Get the appropriate tag name based on context
        tag_name = self._get_tag_name(version)

        try:
            # Use GitHub CLI to list all tags and check if our version exists
            repo_path = self.github_repo if self.github_repo else ":owner/:repo"
            tags_output = self.run_command(f"gh api repos/{repo_path}/tags --paginate --jq '.[].name'")
            remote_tags = tags_output.split("\n") if tags_output else []

            if tag_name in remote_tags:
                return True

            # Fallback: check local git tags (for local development)
            local_tags = self.run_command("git tag -l")
            return tag_name in local_tags.split("\n")

        except Exception:
            # If GitHub CLI fails, fallback to local git tags only
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
        tag_name = self._get_tag_name(version)

        try:
            # Check if release exists
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
        # Remove any RC suffix for parsing
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
        try:
            # Get all RC tags from GitHub API, sort by version descending
            repo_path = self.github_repo if self.github_repo else ":owner/:repo"
            tags_output = self.run_command(f"gh api repos/{repo_path}/tags --paginate --jq '.[].name'")
            if not tags_output:
                return None

            # Create pattern based on context (plugin vs main project)
            if self.plugin_mode and self.plugin_name:
                plugin_tag_name = self.plugin_name.replace("_", "-")
                rc_pattern = rf"^{re.escape(plugin_tag_name)}-v\d+\.\d+\.\d+-RC\.\d+$"
                tag_prefix_len = len(f"{plugin_tag_name}-v")
            else:
                rc_pattern = r"^v\d+\.\d+\.\d+-RC\.\d+$"
                tag_prefix_len = 1  # Just 'v'

            rc_tags = [tag for tag in tags_output.split("\n") if re.match(rc_pattern, tag)]

            if not rc_tags:
                return None

            # Sort by version (extract version numbers for sorting)
            rc_tags.sort(key=lambda x: [int(i) for i in re.findall(r"\d+", x)], reverse=True)

            # Return without prefix
            return rc_tags[0][tag_prefix_len:] if rc_tags else None

        except Exception:
            return None

    def generate_rc_versions(self, project_folder_path: str) -> Tuple[str, str]:
        """
        Generate both the package version (final) and RC tag (for git) following
        'build once, promote many' principle.

        Returns:
            Tuple[str, str]: (package_version, rc_tag)
        """
        project_dir = Path(project_folder_path)
        current_version = self.get_current_version(project_dir)

        # Check if current version is already an RC
        rc_pattern = rf"-{RC_VERSION_SUFFIX}\.(\d+)$"
        rc_match = re.search(rc_pattern, current_version)

        if rc_match:
            # Current version is already an RC, use base version for package
            package_version = re.sub(rc_pattern, "", current_version)
            base_version = package_version
            rc_number = int(rc_match.group(1))

            # Find the highest existing RC number for this base version
            while True:
                next_rc_number = rc_number + 1
                candidate_rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.{next_rc_number}"
                if not self.check_tag_exists(candidate_rc_version):
                    rc_tag = self._get_tag_name(candidate_rc_version)
                    break
                rc_number = next_rc_number
        else:
            # Current version is not an RC
            if self.check_tag_exists(current_version):
                # Version exists as tag, increment patch for next version
                major, minor, patch = self.parse_version(current_version)
                new_patch = patch + 1
                package_version = f"{major}.{minor}.{new_patch}"
            else:
                # Use current version as package version
                package_version = current_version

            # Find the first available RC number for this base version
            rc_number = 1
            while True:
                candidate_rc_version = f"{package_version}-{RC_VERSION_SUFFIX}.{rc_number}"
                if not self.check_tag_exists(candidate_rc_version):
                    rc_tag = self._get_tag_name(candidate_rc_version)
                    break
                rc_number += 1

        return package_version, rc_tag

    def determine_rc_to_promote(self, input_rc_version: Optional[str] = None) -> Tuple[str, str]:
        """
        Determine which RC version to promote to GA.

        Args:
            input_rc_version: Optional RC version provided by user

        Returns:
            Tuple[str, str]: (rc_version, stable_version)
        """
        if input_rc_version:
            # Validate format
            if not self.validate_rc_version_format(input_rc_version):
                raise ValueError(f"Invalid RC version format: {input_rc_version}. Expected format: x.y.z-RC.N")

            # Check if RC exists and is a pre-release
            exists, is_prerelease = self.check_release_exists(input_rc_version)
            if not exists:
                raise ValueError(f"RC version v{input_rc_version} not found in GitHub releases")

            if not is_prerelease:
                raise ValueError(f"Release v{input_rc_version} is not marked as pre-release")

            rc_version = input_rc_version
        else:
            rc_version = self.get_latest_rc_version()

            if not rc_version:
                raise ValueError("No RC versions found in GitHub releases")

        # Generate stable version by removing RC suffix
        stable_version = re.sub(rf"-{RC_VERSION_SUFFIX}\.\d+$", "", rc_version)

        return rc_version, stable_version


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
    print("  detect-plugins --plugin-mode")
    print("    Purpose: Analyze git changes to identify which plugins have been modified")
    print("    Usage:   Used in CI matrix workflows to determine which plugins need RC creation")
    print("    Action:  READ-ONLY - No changes to remote repositories, only analyzes local git changes")
    print("    JSON Response Fields:")
    print(
        '             - plugins: Array of changed plugin names (e.g., ["provisioner_examples_plugin"] or [] if no changes)'
    )
    print("             - repository: Repository being analyzed")
    print("    Example: python version_manager.py detect-plugins --plugin-mode")
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
    """Main function that handles both RC generation and GA promotion logic."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    action = sys.argv[1]

    # Check for plugin mode flag
    plugin_mode = "--plugin-mode" in sys.argv
    if plugin_mode:
        sys.argv.remove("--plugin-mode")

    # Check for github-repo flag
    github_repo = None
    github_repo_index = None
    for i, arg in enumerate(sys.argv):
        if arg == "--github-repo" and i + 1 < len(sys.argv):
            github_repo = sys.argv[i + 1]
            github_repo_index = i
            break

    if github_repo_index is not None:
        # Remove both --github-repo and its value
        sys.argv.pop(github_repo_index + 1)  # Remove the value first
        sys.argv.pop(github_repo_index)  # Then remove the flag

    # For detect-plugins action, we don't require plugin context
    require_context = action != "detect-plugins"

    # For generate and promote commands, pass project_folder_path for better plugin detection
    project_path_hint = None
    if action == "generate" and len(sys.argv) >= 3:
        project_path_hint = sys.argv[2]
    elif action == "promote" and len(sys.argv) >= 3:
        project_path_hint = sys.argv[2]

    version_manager = VersionManager(
        plugin_mode=plugin_mode,
        require_plugin_context=require_context,
        github_repo=github_repo,
        project_path_hint=project_path_hint,
    )

    try:
        if action == "generate":
            if len(sys.argv) != 3:
                error_response = {
                    "error": "generate command requires exactly one argument",
                    "usage": "python version_manager.py generate <project_folder_path> [--plugin-mode] [--github-repo <owner/repo>]",
                    "purpose": "Calculate RC versions for creating release candidates",
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)

            project_folder_path = sys.argv[2]

            # Validate project path and read package name from pyproject.toml
            try:
                package_name = version_manager.validate_project_path(project_folder_path)
            except ValueError as e:
                error_response = {
                    "error": str(e),
                    "action": "generate",
                    "project_path": project_folder_path,
                    "requirement": "Project path must contain a valid pyproject.toml with [tool.poetry] section and 'name' attribute",
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)

            package_version, rc_tag = version_manager.generate_rc_versions(project_folder_path)

            # Create structured JSON response
            response_data = {
                "package_version": package_version,
                "rc_tag": rc_tag,
                "plugin_name": version_manager.plugin_name or "",
                "package_name": version_manager._get_package_name(),
                "project_folder_path": project_folder_path,
                "is_plugin": plugin_mode,
            }

            json_response = version_manager._output_json_response(response_data)
            print(json_response)

        elif action == "promote":
            if len(sys.argv) < 3:
                error_response = {
                    "error": "promote command requires at least one argument",
                    "usage": "python version_manager.py promote <project_folder_path> [rc_version] [--plugin-mode] [--github-repo <owner/repo>]",
                    "purpose": "Promote existing RC to General Availability",
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)

            project_folder_path = sys.argv[2]
            input_rc_version = sys.argv[3] if len(sys.argv) > 3 else None

            # Validate project path and read package name from pyproject.toml
            try:
                package_name = version_manager.validate_project_path(project_folder_path)
            except ValueError as e:
                error_response = {
                    "error": str(e),
                    "action": "promote",
                    "project_path": project_folder_path,
                    "requirement": "Project path must contain a valid pyproject.toml with [tool.poetry] section and 'name' attribute",
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)

            rc_version, stable_version = version_manager.determine_rc_to_promote(input_rc_version)

            # Create structured JSON response
            response_data = {
                "rc_version": rc_version,
                "stable_version": stable_version,
                "plugin_name": version_manager.plugin_name or "",
                "package_name": version_manager._get_package_name(),
                "is_plugin": plugin_mode,
                "input_rc_version": input_rc_version or "auto-detected",
                "project_folder_path": project_folder_path,
            }

            json_response = version_manager._output_json_response(response_data)
            print(json_response)

        elif action == "detect-plugins":
            # Special action to detect changed plugins - doesn't require specific plugin context
            if not plugin_mode:
                error_response = {
                    "error": "detect-plugins command requires --plugin-mode flag",
                    "usage": "python version_manager.py detect-plugins --plugin-mode [--github-repo <owner/repo>]",
                    "purpose": "Analyze git changes to identify modified plugins for CI matrix",
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)

            affected_plugins = version_manager.get_plugins_from_changes()

            # Create structured JSON response
            response_data = {"plugins": affected_plugins, "repository": version_manager.github_repo or "local"}

            json_response = version_manager._output_json_response(response_data)
            print(json_response)

        else:
            error_response = {
                "error": f"Unknown action '{action}'",
                "available_actions": [
                    {"name": "generate", "description": "Calculate RC versions for release candidate creation"},
                    {"name": "promote", "description": "Promote existing RC to General Availability"},
                    {"name": "detect-plugins", "description": "Detect changed plugins for CI matrix workflows"},
                ],
                "help": "Use 'python version_manager.py' without arguments for full help.",
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)

    except Exception as e:
        error_response = {"error": str(e), "action": action if "action" in locals() else "unknown"}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
