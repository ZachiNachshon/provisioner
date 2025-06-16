#!/usr/bin/env python3
"""
Version Manager Script

This script handles version management for both RC creation and GA promotion.
It encapsulates all RC-related behavior and version validation logic.
"""

import os
import re
import subprocess
import sys
import json
from pathlib import Path
from typing import Tuple, Optional

RC_VERSION_SUFFIX = "RC"


class VersionManager:
    """Manages version calculations and RC validation for release workflows."""
    
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
    
    def run_command(self, cmd: str, cwd: Path = None) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd or Path.cwd(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {cmd}")
            print(f"Error output: {e.stderr}")
            sys.exit(1)

    def get_current_version(self, project_dir: Path) -> str:
        """Get current version from poetry."""
        output = self.run_command("poetry version", cwd=project_dir)
        # Extract version from "package-name x.y.z" format
        version = output.split()[-1]
        return version.strip()

    def check_tag_exists(self, version: str) -> bool:
        """Check if a git tag exists for the given version using GitHub CLI."""
        try:
            # Use GitHub CLI to list all tags and check if our version exists
            tags_output = self.run_command("gh api repos/:owner/:repo/tags --paginate --jq '.[].name'")
            remote_tags = tags_output.split('\n') if tags_output else []
            
            if f"v{version}" in remote_tags:
                return True
                
            # Fallback: check local git tags (for local development)
            local_tags = self.run_command("git tag -l")
            return f"v{version}" in local_tags.split('\n')
            
        except:
            # If GitHub CLI fails, fallback to local git tags only
            try:
                tags = self.run_command("git tag -l")
                return f"v{version}" in tags.split('\n')
            except:
                return False

    def check_release_exists(self, version: str) -> Tuple[bool, bool]:
        """
        Check if a GitHub release exists and if it's a pre-release.
        
        Returns:
            Tuple[bool, bool]: (exists, is_prerelease)
        """
        try:
            # Check if release exists
            result = self.run_command(f'gh release view "v{version}" --json isPrerelease')
            release_data = json.loads(result)
            return True, release_data.get('isPrerelease', False)
        except:
            return False, False

    def validate_rc_version_format(self, rc_version: str) -> bool:
        """Validate RC version format (x.y.z-RC.N)."""
        pattern = r'^\d+\.\d+\.\d+-RC\.\d+$'
        return bool(re.match(pattern, rc_version))

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into major, minor, patch components."""
        # Remove any RC suffix for parsing
        clean_version = re.sub(f'-{RC_VERSION_SUFFIX}\.\d+$', '', version)
        parts = clean_version.split('.')
        
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
            tags_output = self.run_command("gh api repos/:owner/:repo/tags --paginate --jq '.[].name'")
            if not tags_output:
                return None
                
            rc_tags = [
                tag for tag in tags_output.split('\n') 
                if re.match(r'^v\d+\.\d+\.\d+-RC\.\d+$', tag)
            ]
            
            if not rc_tags:
                return None
            
            # Sort by version (remove 'v' prefix for sorting)
            rc_tags.sort(key=lambda x: [int(i) for i in re.findall(r'\d+', x)], reverse=True)
            
            # Return without 'v' prefix
            return rc_tags[0][1:] if rc_tags else None
            
        except Exception as e:
            print(f"Error getting latest RC version: {e}")
            return None

    def generate_rc_versions(self, project_to_release: str) -> Tuple[str, str]:
        """
        Generate both the package version (final) and RC tag (for git) following
        'build once, promote many' principle.
        
        Returns:
            Tuple[str, str]: (package_version, rc_tag)
        """
        print("Calculating release versions using 'build once, promote many' approach")
        
        project_dir = Path(project_to_release)
        current_version = self.get_current_version(project_dir)
        print(f"Current version: {current_version}")
        
        # Check if current version is already an RC
        rc_pattern = f'-{RC_VERSION_SUFFIX}\.(\d+)$'
        rc_match = re.search(rc_pattern, current_version)
        
        if rc_match:
            # Current version is already an RC, use base version for package
            package_version = re.sub(rc_pattern, '', current_version)
            base_version = package_version
            rc_number = int(rc_match.group(1))
            
            # Find the highest existing RC number for this base version
            while True:
                next_rc_number = rc_number + 1
                candidate_rc_tag = f"{base_version}-{RC_VERSION_SUFFIX}.{next_rc_number}"
                if not self.check_tag_exists(candidate_rc_tag):
                    rc_tag = candidate_rc_tag
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
                candidate_rc_tag = f"{package_version}-{RC_VERSION_SUFFIX}.{rc_number}"
                if not self.check_tag_exists(candidate_rc_tag):
                    rc_tag = candidate_rc_tag
                    break
                rc_number += 1
        
        print(f"Package version (final): {package_version}")
        print(f"RC git tag: {rc_tag}")
        print("Packages will be built with final version, git tag will use RC suffix")
        
        return package_version, rc_tag

    def determine_rc_to_promote(self, input_rc_version: Optional[str] = None) -> Tuple[str, str]:
        """
        Determine which RC version to promote to GA.
        
        Args:
            input_rc_version: Optional RC version provided by user
            
        Returns:
            Tuple[str, str]: (rc_version, stable_version)
        """
        print("Determining RC version to promote")
        
        if input_rc_version:
            print(f"Using provided RC version: {input_rc_version}")
            
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
            print("Auto-detecting latest RC version...")
            rc_version = self.get_latest_rc_version()
            
            if not rc_version:
                raise ValueError("No RC versions found in GitHub releases")
            
            print(f"Auto-detected latest RC version: {rc_version}")
        
        # Generate stable version by removing RC suffix
        stable_version = re.sub(f'-{RC_VERSION_SUFFIX}\.\d+$', '', rc_version)
        
        print(f"Final RC version to promote: {rc_version} -> {stable_version}")
        return rc_version, stable_version


def main():
    """Main function that handles both RC generation and GA promotion logic."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python version_manager.py generate <project_to_release>")
        print("  python version_manager.py promote [rc_version]")
        sys.exit(1)
    
    action = sys.argv[1]
    version_manager = VersionManager()
    
    try:
        if action == "generate":
            if len(sys.argv) != 3:
                print("Usage: python version_manager.py generate <project_to_release>")
                sys.exit(1)
            
            project_to_release = sys.argv[2]
            print(f"Calculating release versions for project: {project_to_release}")
            
            package_version, rc_tag = version_manager.generate_rc_versions(project_to_release)
            
            print(f"Final package version: {package_version}")
            print(f"RC git tag: {rc_tag}")
            
            # Set GitHub Action outputs
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"package_version={package_version}\n")
                    f.write(f"rc_tag={rc_tag}\n")
            
        elif action == "promote":
            input_rc_version = sys.argv[2] if len(sys.argv) > 2 else None
            
            rc_version, stable_version = version_manager.determine_rc_to_promote(input_rc_version)
            
            print(f"RC version: {rc_version}")
            print(f"Stable version: {stable_version}")
            
            # Set GitHub Action outputs
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"rc_version={rc_version}\n")
                    f.write(f"stable_version={stable_version}\n")
        
        else:
            print(f"Unknown action: {action}")
            print("Available actions: generate, promote")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 