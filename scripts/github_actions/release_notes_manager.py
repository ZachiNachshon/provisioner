#!/usr/bin/env python3
"""
Release Notes Manager Script

This script handles extraction of release notes from draft releases and
preparation of GA release notes. It encapsulates all release notes logic
for the GA promotion workflow.
"""

import os
import re
import subprocess
import sys
from typing import Optional, Tuple


class ReleaseNotesManager:
    """Manages release notes extraction and preparation for GA releases."""

    def __init__(self, plugin_mode: bool = False):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.plugin_mode = plugin_mode
        self.plugin_name = None

        if plugin_mode:
            self.plugin_name = self._detect_plugin_context()
            if not self.plugin_name:
                print("Warning: Plugin mode enabled but could not detect plugin context")

    def _detect_plugin_context(self) -> Optional[str]:
        """Detect plugin context from current directory using dynamic discovery."""
        import re
        from pathlib import Path

        cwd = Path.cwd()

        # Find plugins directory
        plugins_dir = None
        if cwd.name == "plugins":
            plugins_dir = cwd
        elif cwd.parent.name == "plugins":
            plugins_dir = cwd.parent
        elif "plugins" in cwd.parts:
            for i, part in enumerate(cwd.parts):
                if part == "plugins":
                    plugins_dir = Path("/".join(cwd.parts[: i + 1]))
                    break

        if not plugins_dir or not plugins_dir.exists():
            return None

        # Get all available plugins
        plugin_candidates = []
        for item in plugins_dir.iterdir():
            if item.is_dir() and re.match(r"^provisioner_.*_plugin$", item.name) and (item / "pyproject.toml").exists():
                plugin_candidates.append(item.name)

        # Check which plugin matches current context
        for plugin in plugin_candidates:
            if plugin in str(cwd):
                return plugin

        return None

    def _format_tag(self, version: str) -> str:
        """Format version into appropriate tag name based on context."""
        if self.plugin_mode and self.plugin_name:
            plugin_tag_name = self.plugin_name.replace("_", "-")
            if version.startswith("v"):
                return f"{plugin_tag_name}-{version}"
            else:
                return f"{plugin_tag_name}-v{version}"
        else:
            return f"v{version}" if not version.startswith("v") else version

    def run_command(self, cmd: str) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {cmd}")
            print(f"Error output: {e.stderr}")
            raise

    def check_release_exists(self, tag: str) -> bool:
        """Check if a GitHub release exists for the given tag."""
        try:
            self.run_command(f'gh release view "{tag}"')
            return True
        except Exception:
            return False

    def get_release_notes(self, tag: str) -> Optional[str]:
        """Get release notes from a GitHub release."""
        try:
            result = self.run_command(f"gh release view \"{tag}\" --json body --jq '.body'")
            return result if result and result != "null" else None
        except Exception:
            return None

    def parse_version_components(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into major, minor, patch components."""
        # Remove any RC suffix for parsing
        clean_version = re.sub(r"-RC\.\d+$", "", version)
        parts = clean_version.split(".")

        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version numbers in: {version}")

    def find_draft_release(self, stable_version: str) -> Optional[Tuple[str, str]]:
        """
        Find a draft release that might contain relevant release notes.

        Args:
            stable_version: The stable version we're promoting to (e.g., "0.1.20")

        Returns:
            Optional[Tuple[str, str]]: (draft_tag, release_notes) if found, None otherwise
        """
        print("Looking for draft release notes")

        # Parse version components
        major, minor, patch = self.parse_version_components(stable_version)

        # Try different possible draft versions
        draft_candidates = [
            self._format_tag(f"{stable_version}-draft"),  # Current version with -draft suffix
            self._format_tag(f"{major}.{minor + 1}.0-draft"),  # Next minor version with -draft suffix
            self._format_tag(f"{major + 1}.0.0-draft"),  # Next major version with -draft suffix
        ]

        for draft_tag in draft_candidates:
            print(f"Checking for draft release: {draft_tag}")

            if self.check_release_exists(draft_tag):
                print(f"Found draft release: {draft_tag}")
                release_notes = self.get_release_notes(draft_tag)

                if release_notes:
                    print("Successfully extracted release notes from draft")
                    return draft_tag, release_notes
                else:
                    print(f"Draft release {draft_tag} exists but has no release notes")

        print("No draft release with notes found")
        return None

    def get_rc_release_notes(self, rc_version: str) -> Optional[str]:
        """Get release notes from RC release as fallback."""
        rc_tag = self._format_tag(rc_version)
        print(f"Getting release notes from RC release: {rc_tag}")

        rc_notes = self.get_release_notes(rc_tag)
        if rc_notes:
            print("Successfully extracted release notes from RC")
            return rc_notes
        else:
            print("No release notes available from RC")
            return None

    def prepare_ga_release_notes(
        self, rc_version: str, stable_version: str, output_file: str = "ga_release_notes.md"
    ) -> str:
        """
        Prepare comprehensive release notes for GA release.

        Args:
            rc_version: The RC version being promoted (e.g., "0.1.20-RC.5")
            stable_version: The stable version being created (e.g., "0.1.20")
            output_file: Output file name for the release notes

        Returns:
            str: Path to the created release notes file
        """
        print(f"Preparing GA release notes for v{stable_version}")

        # Try to find draft release notes first
        draft_result = self.find_draft_release(stable_version)

        if draft_result:
            draft_tag, draft_notes = draft_result
            print(f"Using release notes from draft release: {draft_tag}")

            # Create GA release notes with draft content
            with open(output_file, "w") as f:
                f.write(f"**Promoted from Release Candidate v{rc_version}**\n\n")
                f.write(draft_notes)

            print(f"Created GA release notes using draft: {draft_tag}")

        else:
            print("Using release notes from RC release (fallback)")

            # Fallback to RC notes
            rc_notes = self.get_rc_release_notes(rc_version)

            with open(output_file, "w") as f:
                f.write(f"Promoted from Release Candidate v{rc_version}\n\n")
                f.write("### Changes in this release:\n\n")

                if rc_notes:
                    f.write(rc_notes)
                else:
                    f.write("No release notes available from RC")

            print("Created GA release notes using RC fallback")

        # Display final release notes
        print("\nFinal release notes for GA:")
        with open(output_file, "r") as f:
            print(f.read())

        return output_file

    def extract_draft_notes_only(self, stable_version: str, output_file: str = "draft_release_notes.md") -> bool:
        """
        Extract release notes from draft release without creating GA notes.

        Args:
            stable_version: The stable version to look for drafts
            output_file: Output file name for the extracted notes

        Returns:
            bool: True if draft notes were found and extracted, False otherwise
        """
        draft_result = self.find_draft_release(stable_version)

        if draft_result:
            draft_tag, draft_notes = draft_result

            with open(output_file, "w") as f:
                f.write(draft_notes)

            print(f"Extracted draft notes from {draft_tag} to {output_file}")
            return True

        print("No draft release notes found")
        return False


def main():
    """Main function that handles release notes operations."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python release_notes_manager.py prepare <rc_version> <stable_version> [output_file] [--plugin-mode]")
        print("  python release_notes_manager.py extract <stable_version> [output_file] [--plugin-mode]")
        sys.exit(1)

    # Check for plugin mode flag
    plugin_mode = "--plugin-mode" in sys.argv
    if plugin_mode:
        sys.argv.remove("--plugin-mode")

    action = sys.argv[1]
    notes_manager = ReleaseNotesManager(plugin_mode=plugin_mode)

    try:
        if action == "prepare":
            if len(sys.argv) < 4:
                print(
                    "Usage: python release_notes_manager.py prepare <rc_version> <stable_version> [output_file] [--plugin-mode]"
                )
                sys.exit(1)

            rc_version = sys.argv[2]
            stable_version = sys.argv[3]
            output_file = sys.argv[4] if len(sys.argv) > 4 else "ga_release_notes.md"

            result_file = notes_manager.prepare_ga_release_notes(rc_version, stable_version, output_file)
            print(f"GA release notes prepared: {result_file}")

        elif action == "extract":
            if len(sys.argv) < 3:
                print("Usage: python release_notes_manager.py extract <stable_version> [output_file] [--plugin-mode]")
                sys.exit(1)

            stable_version = sys.argv[2]
            output_file = sys.argv[3] if len(sys.argv) > 3 else "draft_release_notes.md"

            success = notes_manager.extract_draft_notes_only(stable_version, output_file)

            if success:
                print(f"Draft release notes extracted: {output_file}")
            else:
                print("No draft release notes found")
                sys.exit(1)

        else:
            print(f"Unknown action: {action}")
            print("Available actions: prepare, extract")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
