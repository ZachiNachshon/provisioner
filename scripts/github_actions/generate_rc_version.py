#!/usr/bin/env python3
"""
Generate RC Version Script

This script purely calculates the next RC version based on current version and existing tags.
It does not modify any files - that responsibility belongs to the build tools.
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


def generate_rc_version(project_to_release: str) -> str:
    """Generate the RC version based on current version and existing tags."""
    print("Calculating next RC version")
    
    project_dir = Path(project_to_release)
    current_version = get_current_version(project_dir)
    print(f"Current version: {current_version}")
    
    # Check if current version is already an RC
    rc_pattern = f'-{RC_VERSION_SUFFIX}\.(\d+)$'
    rc_match = re.search(rc_pattern, current_version)
    
    if rc_match:
        # Current version is already an RC, increment RC number
        base_version = re.sub(rc_pattern, '', current_version)
        rc_number = int(rc_match.group(1))
        
        # Find the highest existing RC number for this base version
        while True:
            next_rc_number = rc_number + 1
            candidate_rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.{next_rc_number}"
            if not check_tag_exists(candidate_rc_version):
                rc_version = candidate_rc_version
                break
            rc_number = next_rc_number
    else:
        # Current version is not an RC
        if check_tag_exists(current_version):
            # Version exists as tag, increment patch and add RC
            major, minor, patch = parse_version(current_version)
            new_patch = patch + 1
            base_version = f"{major}.{minor}.{new_patch}"
        else:
            # Use current version as base
            base_version = current_version
        
        # Find the first available RC number for this base version
        rc_number = 1
        while True:
            candidate_rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.{rc_number}"
            if not check_tag_exists(candidate_rc_version):
                rc_version = candidate_rc_version
                break
            rc_number += 1
    
    print(f"Calculated RC version: {rc_version}")
    return rc_version


def main():
    """Main function that calculates and returns RC version information."""
    if len(sys.argv) != 2:
        print("Usage: python generate_rc_version.py <project_to_release>")
        sys.exit(1)
    
    project_to_release = sys.argv[1]
    
    print(f"Calculating RC version for project: {project_to_release}")
    
    # Generate RC version (read-only operation)
    rc_version = generate_rc_version(project_to_release)
    
    print(f"Next RC version calculated: {rc_version}")
    print("Note: Version updates and builds will be handled by package_deployer.sh")
    
    # Set GitHub Action outputs
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"rc_version={rc_version}\n")
    else:
        # For local testing
        print(f"rc_version={rc_version}")


if __name__ == "__main__":
    main() 