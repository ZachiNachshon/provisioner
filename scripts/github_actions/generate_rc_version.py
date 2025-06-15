#!/usr/bin/env python3
"""
Generate RC Version Script

This script calculates the final stable version for packages and RC tag for git.
Following "build once, promote many" principle - packages are built with final version,
only git tags use RC suffix for channel management.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

RC_VERSION_SUFFIX = "RC"

def run_command(cmd: str, cwd: Path = None) -> str:
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


def get_current_version(project_dir: Path) -> str:
    """Get current version from poetry."""
    output = run_command("poetry version", cwd=project_dir)
    # Extract version from "package-name x.y.z" format
    version = output.split()[-1]
    return version.strip()


def check_tag_exists(version: str) -> bool:
    """Check if a git tag exists for the given version using GitHub CLI."""
    try:
        # Use GitHub CLI to list all tags and check if our version exists
        # This queries the remote repository without fetching all history
        tags_output = run_command("gh api repos/:owner/:repo/tags --paginate --jq '.[].name'")
        remote_tags = tags_output.split('\n') if tags_output else []
        
        if f"v{version}" in remote_tags:
            return True
            
        # Fallback: check local git tags (for local development)
        local_tags = run_command("git tag -l")
        return f"v{version}" in local_tags.split('\n')
        
    except:
        # If GitHub CLI fails, fallback to local git tags only
        try:
            tags = run_command("git tag -l")
            return f"v{version}" in tags.split('\n')
        except:
            return False


def parse_version(version: str) -> tuple:
    """Parse version string into major, minor, patch components."""
    # Remove any RC suffix for parsing
    clean_version = re.sub(f'-{RC_VERSION_SUFFIX}\.\d+$', '', version)
    parts = clean_version.split('.')
    
    if len(parts) != 3:
        print(f"Error: Invalid version format: {version}")
        sys.exit(1)
    
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        print(f"Error: Invalid version numbers in: {version}")
        sys.exit(1)


def generate_release_versions(project_to_release: str) -> tuple:
    """
    Generate both the package version (final) and RC tag (for git) following
    'build once, promote many' principle.
    
    Returns:
        tuple: (package_version, rc_tag)
        - package_version: Final version for packages (e.g., "1.0.0")
        - rc_tag: RC tag for git (e.g., "1.0.0-RC.1")
    """
    print("Calculating release versions using 'build once, promote many' approach")
    
    project_dir = Path(project_to_release)
    current_version = get_current_version(project_dir)
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
            if not check_tag_exists(candidate_rc_tag):
                rc_tag = candidate_rc_tag
                break
            rc_number = next_rc_number
    else:
        # Current version is not an RC
        if check_tag_exists(current_version):
            # Version exists as tag, increment patch for next version
            major, minor, patch = parse_version(current_version)
            new_patch = patch + 1
            package_version = f"{major}.{minor}.{new_patch}"
        else:
            # Use current version as package version
            package_version = current_version
        
        # Find the first available RC number for this base version
        rc_number = 1
        while True:
            candidate_rc_tag = f"{package_version}-{RC_VERSION_SUFFIX}.{rc_number}"
            if not check_tag_exists(candidate_rc_tag):
                rc_tag = candidate_rc_tag
                break
            rc_number += 1
    
    print(f"Package version (final): {package_version}")
    print(f"RC git tag: {rc_tag}")
    print("Packages will be built with final version, git tag will use RC suffix")
    
    return package_version, rc_tag


def main():
    """Main function that calculates release versions using build-once approach."""
    if len(sys.argv) != 2:
        print("Usage: python generate_rc_version.py <project_to_release>")
        sys.exit(1)
    
    project_to_release = sys.argv[1]
    
    print(f"Calculating release versions for project: {project_to_release}")
    
    # Generate versions using build-once approach
    package_version, rc_tag = generate_release_versions(project_to_release)
    
    print(f"Final package version: {package_version}")
    print(f"RC git tag: {rc_tag}")
    print("Note: package_deployer.sh will build packages with the final version")
    
    # Set GitHub Action outputs
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"package_version={package_version}\n")
            f.write(f"rc_tag={rc_tag}\n")
    else:
        # For local testing
        print(f"package_version={package_version}")
        print(f"rc_tag={rc_tag}")


if __name__ == "__main__":
    main() 