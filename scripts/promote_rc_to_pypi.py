#!/usr/bin/env python3
"""
Promote RC to Stable Version Script

This script handles the promotion of RC versions to stable versions and publishes to PyPI.
It replaces the bash script in the "Promote RC to Stable Version" step.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: Path = None, env: dict = None) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd or Path.cwd(), capture_output=True, text=True, check=True, env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def convert_rc_to_stable(rc_version: str) -> str:
    """Convert RC version to stable version by removing RC suffix."""
    # Remove -RC.X suffix
    stable_version = re.sub(r"-RC\.\d+$", "", rc_version)
    print(f"Converting RC version {rc_version} to stable version {stable_version}")
    return stable_version


def check_pypi_version_exists(package_name: str, version: str) -> bool:
    """Check if a version already exists on PyPI."""
    try:
        # Use pip index to check if version exists
        output = run_command(f"pip index versions {package_name}")
        return version in output
    except Exception:
        # If command fails, assume version doesn't exist
        return False


def verify_pypi_availability(stable_version: str):
    """Verify that the stable version doesn't already exist on PyPI."""
    print(f"Checking if version {stable_version} already exists on PyPI...")

    # Check provisioner runtime
    if check_pypi_version_exists("provisioner", stable_version):
        print(f"Error: Version {stable_version} already exists on PyPI for provisioner")
        sys.exit(1)

    # Check provisioner shared
    if check_pypi_version_exists("provisioner-shared", stable_version):
        print(f"Error: Version {stable_version} already exists on PyPI for provisioner-shared")
        sys.exit(1)

    print(f"Version {stable_version} is available for publishing")


def update_poetry_version(version: str, project_dir: Path):
    """Update poetry version in the specified project directory."""
    run_command(f"poetry version {version}", cwd=project_dir)


def get_poetry_version(project_dir: Path) -> str:
    """Get current version from poetry."""
    output = run_command("poetry version", cwd=project_dir)
    return output.split()[-1].strip()


def update_manifest_version(version: str, project_dir: Path):
    """Update version in manifest.json file."""
    manifest_path = project_dir / "resources" / "manifest.json"

    if not manifest_path.exists():
        print(f"Warning: manifest.json not found at {manifest_path}")
        return

    print(f"Updating manifest.json version to {version} in {project_dir}")

    # Read current manifest
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    # Update version
    manifest_data["version"] = version

    # Write updated manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)


def update_shared_dependency(project_dir: Path, shared_version: str):
    """Update shared package dependency version in pyproject.toml."""
    update_script = Path("../scripts/update_shared_version.py")
    pyproject_path = project_dir / "pyproject.toml"

    if update_script.exists():
        run_command(
            f"python {update_script} --file_path {pyproject_path} --package_name provisioner-shared --new_version '^{shared_version}'",
            cwd=project_dir.parent,
        )
    else:
        print(f"Warning: update_shared_version.py not found at {update_script}")


def publish_package(project_dir: Path, pypi_token: str):
    """Publish package to PyPI using the publisher script."""
    publisher_script = Path("../scripts/github_actions/package_deployer.sh")

    if not publisher_script.exists():
        print(f"Error: Publisher script not found at {publisher_script}")
        sys.exit(1)

    # Set up environment with PyPI token
    env = os.environ.copy()
    env["PYPI_API_TOKEN"] = pypi_token

    # Run publisher script
    run_command(f"{publisher_script} publish --build-type wheel --release-type pypi -y", cwd=project_dir, env=env)


def publish_shared_package(stable_version: str, pypi_token_shared: str):
    """Publish provisioner-shared package with stable version."""
    print("\n=== Publishing provisioner-shared package ===")

    shared_dir = Path("provisioner_shared")

    # Set stable version
    update_poetry_version(stable_version, shared_dir)
    shared_ver = get_poetry_version(shared_dir)

    # Update version in manifest.json
    update_manifest_version(shared_ver, shared_dir)

    print(f"Publishing provisioner-shared v{shared_ver} to PyPI")
    publish_package(shared_dir, pypi_token_shared)

    return shared_ver


def publish_runtime_package(project_name: str, stable_version: str, shared_version: str, pypi_token: str):
    """Publish runtime package with stable version."""
    print(f"\n=== Publishing {project_name} package ===")

    project_dir = Path(project_name)

    # Set stable version
    update_poetry_version(stable_version, project_dir)
    runtime_ver = get_poetry_version(project_dir)

    # Update version in manifest.json
    update_manifest_version(runtime_ver, project_dir)

    # Update shared version in the runtime pyproject.toml
    update_shared_dependency(project_dir, shared_version)

    print(f"Publishing {project_name} v{runtime_ver} to PyPI")
    publish_package(project_dir, pypi_token)

    return runtime_ver


def main():
    """Main function that handles the RC to stable promotion."""
    if len(sys.argv) != 4:
        print("Usage: python promote_rc_to_pypi.py <project_name> <rc_version> <pypi_tokens>")
        print("Example: python promote_rc_to_pypi.py provisioner 1.0.0-RC.1 'token1,token2'")
        sys.exit(1)

    project_name = sys.argv[1]
    rc_version = sys.argv[2]
    pypi_tokens = sys.argv[3].split(",")

    if len(pypi_tokens) != 2:
        print("Error: Expected 2 PyPI tokens (runtime,shared)")
        sys.exit(1)

    pypi_token_runtime = pypi_tokens[0]
    pypi_token_shared = pypi_tokens[1]

    print("Promoting RC to stable version and publishing to PyPI")
    print(f"Project: {project_name}")
    print(f"RC Version: {rc_version}")

    # Convert RC version to stable version
    stable_version = convert_rc_to_stable(rc_version)

    # Verify the stable version doesn't already exist on PyPI
    verify_pypi_availability(stable_version)

    try:
        # Publish shared package first
        shared_version = publish_shared_package(stable_version, pypi_token_shared)

        # Publish runtime package
        runtime_version = publish_runtime_package(project_name, stable_version, shared_version, pypi_token_runtime)

        print("\n✅ Successfully published:")
        print(f"   - provisioner-shared v{shared_version}")
        print(f"   - {project_name} v{runtime_version}")

        # Set GitHub Action output
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"stable_version={stable_version}\n")
        else:
            # For local testing
            print(f"stable_version={stable_version}")

    except Exception as e:
        print(f"❌ Error during publishing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
