#!/usr/bin/env python3
"""
Post-Release Version Bump Script

This script handles the post-release version bump process after promoting an RC to GA.
It updates project versions to the next development cycle and creates a PR with the changes.

Usage:
    python post_release_version_bump.py --project-name <name> --stable-version <version> [--plugin-mode]

Requirements:
    - poetry (for version management)
    - gh CLI (for PR creation)
    - git (for version control operations)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


class PostReleaseVersionBumper:
    """Handles post-release version bumping for projects."""

    def __init__(self, project_name: str, stable_version: str, plugin_mode: bool = False):
        """
        Initialize the version bumper.

        Args:
            project_name: Name of the project (e.g., 'provisioner' or 'provisioner_examples_plugin')
            stable_version: The stable version that was just released (e.g., '1.2.3')
            plugin_mode: Whether this is a plugin release (affects which files are updated)
        """
        self.project_name = project_name
        self.stable_version = stable_version
        self.plugin_mode = plugin_mode
        self.next_version = self._calculate_next_version(stable_version)
        self.root_dir = Path.cwd()

    def _calculate_next_version(self, version: str) -> str:
        """Calculate the next development version (patch bump)."""
        try:
            major, minor, patch = map(int, version.split("."))
            return f"{major}.{minor}.{patch + 1}"
        except ValueError as e:
            raise ValueError(f"Invalid version format '{version}': {e}")

    def _run_command(
        self, command: list, cwd: Optional[Path] = None, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling."""
        try:
            result = subprocess.run(command, cwd=cwd or self.root_dir, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            raise

    def _update_poetry_version(self, project_dir: Path) -> bool:
        """Update poetry version in the specified project directory."""
        if not project_dir.exists():
            print(f"Warning: Project directory {project_dir} does not exist")
            return False

        pyproject_file = project_dir / "pyproject.toml"
        if not pyproject_file.exists():
            print(f"Warning: pyproject.toml not found in {project_dir}")
            return False

        print(f"Updating poetry version in {project_dir} to {self.next_version}")
        self._run_command(["poetry", "version", self.next_version], cwd=project_dir)
        return True

    def _update_manifest_version(self, project_dir: Path) -> bool:
        """Update version in manifest.json if it exists."""
        manifest_file = project_dir / "resources" / "manifest.json"
        if not manifest_file.exists():
            return False

        try:
            with open(manifest_file, "r") as f:
                data = json.load(f)

            data["version"] = self.next_version

            with open(manifest_file, "w") as f:
                json.dump(data, f, indent=2)

            print(f"Updated manifest.json in {project_dir} to {self.next_version}")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to update manifest.json in {project_dir}: {e}")
            return False

    def _setup_git_config(self) -> None:
        """Configure git user for commits."""
        self._run_command(["git", "config", "--global", "user.email", "zachi.nachshon@gmail.com"])
        self._run_command(["git", "config", "--global", "user.name", "ZachiNachshon"])

    def _stage_project_changes(self, project_dir: Path) -> None:
        """Stage changes for a specific project."""
        manifest_file = project_dir / "resources" / "manifest.json"
        pyproject_file = project_dir / "pyproject.toml"

        # Stage files that exist
        for file_path in [manifest_file, pyproject_file]:
            if file_path.exists():
                self._run_command(["git", "add", str(file_path)])

    def _create_branch_and_pr(self) -> None:
        """Create a new branch and PR with the version changes."""
        branch_name = f"post-release-{self.project_name}-v{self.stable_version}-next-{self.next_version}"

        # Check if there are any changes to commit
        status_result = self._run_command(["git", "status", "--porcelain"], check=False)
        if not status_result.stdout.strip():
            print("No changes to commit")
            return

        # Create and switch to new branch first
        self._run_command(["git", "checkout", "-b", branch_name])

        # Create commit
        commit_message = f"Post-release: bump {self.project_name} to next development version {self.next_version}"
        self._run_command(["git", "commit", "-m", commit_message])

        # Push branch
        self._run_command(["git", "push", "--set-upstream", "origin", branch_name])

        # Create PR without labels to avoid dependency on non-existent labels
        pr_title = f"[skip ci] Post-release: bump {self.project_name} to v{self.next_version}"
        pr_body = f"""Post-release version bump after promoting v{self.stable_version} to General Availability.

**Released:** v{self.stable_version} (promoted from RC, published to GitHub + PyPI)
**Next Development:** v{self.next_version}

This follows the 'build once, promote many' approach - artifacts were not rebuilt."""

        # Create PR without labels to avoid failures
        pr_result = self._run_command(
            ["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--base", "master", "--head", branch_name],
            check=False,
        )

        if pr_result.returncode != 0:
            print(f"Warning: Failed to create PR, but branch {branch_name} was created and pushed")
            print(f"PR creation error: {pr_result.stderr}")
        else:
            print(f"Successfully created PR for post-release version bump: {branch_name}")

    def run(self) -> None:
        """Execute the complete post-release version bump process."""
        print(f"Starting post-release version bump for {self.project_name}")
        print(f"Released version: {self.stable_version}")
        print(f"Next development version: {self.next_version}")
        print(f"Plugin mode: {self.plugin_mode}")

        updated_projects = []

        if self.plugin_mode:
            # For plugins, only update the specific plugin directory
            plugin_dir = self.root_dir / self.project_name
            if plugin_dir.exists():
                print(f"Updating plugin: {self.project_name}")
                plugin_updated = self._update_poetry_version(plugin_dir)
                if plugin_updated:
                    self._update_manifest_version(plugin_dir)
                    updated_projects.append(plugin_dir)
            else:
                print(f"Warning: Plugin directory {plugin_dir} not found")
        else:
            # For main project, update both main project and provisioner_shared
            main_project_dir = self.root_dir / self.project_name
            main_updated = self._update_poetry_version(main_project_dir)
            if main_updated:
                self._update_manifest_version(main_project_dir)
                updated_projects.append(main_project_dir)

            # Update provisioner_shared
            shared_project_dir = self.root_dir / "provisioner_shared"
            shared_updated = self._update_poetry_version(shared_project_dir)
            if shared_updated:
                self._update_manifest_version(shared_project_dir)
                updated_projects.append(shared_project_dir)

        if not updated_projects:
            print("No projects were updated. Exiting.")
            return

        # Setup git and create PR
        self._setup_git_config()

        # Stage changes from all updated projects
        for project_dir in updated_projects:
            self._stage_project_changes(project_dir)

        self._create_branch_and_pr()
        print("Post-release version bump completed successfully!")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Bump project versions for next development cycle after GA release")
    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project that was released (e.g., 'provisioner' or 'provisioner_examples_plugin')",
    )
    parser.add_argument(
        "--stable-version", required=True, help="The stable version that was just released (e.g., '1.2.3')"
    )
    parser.add_argument(
        "--plugin-mode", action="store_true", help="Enable plugin mode (only update the specific plugin)"
    )

    args = parser.parse_args()

    try:
        bumper = PostReleaseVersionBumper(args.project_name, args.stable_version, args.plugin_mode)
        bumper.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
