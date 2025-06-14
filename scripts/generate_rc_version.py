#!/usr/bin/env python3
"""
Generate RC Version Script

This script handles the RC version generation logic from the GitHub Action.
It replaces the bash script in the "Generate RC Version" step.
"""

import json
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
    """Check if a git tag exists for the given version."""
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
    print("Generating RC version")
    
    project_dir = Path(project_to_release)
    current_version = get_current_version(project_dir)
    print(f"Current version: {current_version}")
    
    # Check if current version is already an RC
    rc_pattern = f'-{RC_VERSION_SUFFIX}\.(\d+)$'
    rc_match = re.search(rc_pattern, current_version)
    
    if rc_match:
        # Increment RC number
        base_version = re.sub(rc_pattern, '', current_version)
        rc_number = int(rc_match.group(1))
        new_rc_number = rc_number + 1
        rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.{new_rc_number}"
    else:
        # Check if this version already exists as a tag
        if check_tag_exists(current_version):
            # Version exists, increment patch and add RC
            major, minor, patch = parse_version(current_version)
            new_patch = patch + 1
            base_version = f"{major}.{minor}.{new_patch}"
        else:
            # Use current version as base
            base_version = current_version
        
        rc_version = f"{base_version}-{RC_VERSION_SUFFIX}.1"
    
    print(f"Generated RC version: {rc_version}")
    return rc_version


def update_poetry_version(version: str, project_dir: Path):
    """Update poetry version in the specified project directory."""
    run_command(f"poetry version {version}", cwd=project_dir)


def update_manifest_version(version: str, project_dir: Path):
    """Update version in manifest.json file."""
    manifest_path = project_dir / "resources" / "manifest.json"
    
    if not manifest_path.exists():
        print(f"Warning: manifest.json not found at {manifest_path}")
        return
    
    # Read current manifest
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # Update version
    manifest_data['version'] = version
    
    # Write updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)


def build_wheel_package(project_dir: Path):
    """Build wheel package for the specified project."""
    run_command("poetry build --format wheel", cwd=project_dir)


def main():
    """Main function that replicates the Generate RC Version step."""
    if len(sys.argv) != 2:
        print("Usage: python generate_rc_version.py <project_to_release>")
        sys.exit(1)
    
    project_to_release = sys.argv[1]
    
    print(f"Generating RC version for {project_to_release}")
    
    # Generate RC version
    rc_version = generate_rc_version(project_to_release)
    
    # Update poetry version to RC
    project_dir = Path(project_to_release)
    update_poetry_version(rc_version, project_dir)
    
    # Update version in manifest.json
    update_manifest_version(rc_version, project_dir)
    
    # Also update shared package to RC version
    shared_dir = Path("provisioner_shared")
    if shared_dir.exists():
        update_poetry_version(rc_version, shared_dir)
        update_manifest_version(rc_version, shared_dir)
    
    # Build wheel packages for RC
    build_wheel_package(project_dir)
    
    if shared_dir.exists():
        build_wheel_package(shared_dir)
    
    # Set GitHub Action outputs
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"rc_version={rc_version}\n")
            f.write(f"project_name={project_to_release}\n")
    else:
        # For local testing
        print(f"rc_version={rc_version}")
        print(f"project_name={project_to_release}")


if __name__ == "__main__":
    main() 