#!/usr/bin/env python3

import argparse
import os
import pathlib
import subprocess
import sys
import tarfile
from typing import List, Optional, Tuple

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.resolve())
DEFAULT_POETRY_DOCKER_FOLDER_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/poetry"
DEFAULT_POETRY_DOCKERFILE_FILE_PATH = f"{DEFAULT_POETRY_DOCKER_FOLDER_PATH}/Dockerfile"

DEFAULT_CONTAINER_PROJECT_PATH = "/app"
DEFAULT_POETRY_IMAGE_NAME = "provisioner-poetry-e2e"
DEFAULT_POETRY_TAGGED_IMAGE_NAME = "provisioner-poetry-e2e:latest"
DEFAULT_E2E_DOCKER_ESSENTIAL_FILES_ARCHIVE_NAME = "e2e_docker_essential_files.tar.gz"


def should_build_image_before_tests() -> bool:
    return os.getenv("PROVISIONER_BUILD_IMAGE_BEFORE_TESTS", "false").lower() == "true"


def get_project_mounted_volumes() -> dict:
    return [
        "provisioner",
        "provisioner_shared",
        "plugins",
        "scripts",
        ".coveragerc",
        "conftest.py",
        "Makefile",
        "poetry.lock",
        "poetry.toml",
        "pytest.ini",
    ]


def get_test_container_volumes() -> List[str]:
    project_root = resolve_repo_path()
    folders_to_mount = get_project_mounted_volumes()
    result = [f"{os.path.join(project_root, folder)}:/app/{folder}" for folder in folders_to_mount]
    return result


def resolve_repo_path():
    """Resolve the absolute path of the repository."""
    current_dir = os.path.abspath(os.getcwd())
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, ".git")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise RuntimeError("Repository root not found.")


def run(cmd: List[str], is_build: bool = False) -> Tuple[int, str]:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    # Store all output lines
    output_lines = []

    # Stream output in real-time and store it
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            line = output.strip()
            output_lines.append(line)
            if is_build:
                print(line)

    return process.poll(), "\n".join(output_lines)


def _run_docker_container(
    image_name: str, test_target: Optional[str] = None, only_e2e: bool = True, report: bool = False
):

    mount_vols = get_test_container_volumes()
    vol_list = []
    for vol in mount_vols:
        vol_list.append("-v")
        vol_list.append(vol)

    run_tests_cmd = [
        "docker",
        "run",
        "--network=host",
        "--rm",
        "-it",
        "--name",
        image_name,
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        *vol_list,
        "-w",
        "/app",
        image_name,
        test_target if test_target else "",
        "--only-e2e" if only_e2e else "" "--report" if report else "",
    ]

    if test_target:
        print(f"\n🧪 Running test: {test_target}\n")
    else:
        print("\n🧪 Running tests suite...\n")

    exit_code, output = run(run_tests_cmd)
    if exit_code == 0:
        print(output)
        print(f"\n✅ Test run on image {image_name} executed successfully!")
    else:
        print(f"\n❌ Test run failed on image: {image_name}, output: {output}")
        sys.exit(1)


def get_e2e_docker_essentials_files_paths() -> List[str]:
    repo_path = resolve_repo_path()
    runtime_path = os.path.join(repo_path, "provisioner")
    shared_path = os.path.join(repo_path, "provisioner_shared")
    plugins_path = os.path.join(repo_path, "plugins")

    result = []

    # Root
    result.append(os.path.join(repo_path, "pyproject.toml"))
    result.append(os.path.join(repo_path, "poetry.toml"))
    result.append(os.path.join(repo_path, "Makefile"))
    result.append(os.path.join(repo_path, "scripts"))

    # Runtime
    result.append(os.path.join(runtime_path, "pyproject.toml"))
    result.append(os.path.join(runtime_path, "poetry.toml"))

    # Shared
    result.append(os.path.join(shared_path, "components", "__init__.py"))
    result.append(os.path.join(shared_path, "framework", "__init__.py"))
    result.append(os.path.join(shared_path, "resources", "__init__.py"))
    result.append(os.path.join(shared_path, "pyproject.toml"))
    result.append(os.path.join(shared_path, "poetry.toml"))

    # Plugins
    for plugin_name in os.listdir(plugins_path):
        plugin_path = os.path.join(plugins_path, plugin_name)
        if os.path.isdir(plugin_path) and plugin_name.endswith("_plugin"):
            # Add the internal plugin folder as empty folder marker
            # result.append(os.path.join(plugin_path, plugin_path, "")) # Empty directory marker
            result.append(os.path.join(plugin_path, plugin_name, "__init__.py"))
            result.append(os.path.join(plugin_path, "pyproject.toml"))
            result.append(os.path.join(plugin_path, "poetry.toml"))

    return result


def create_project_essentials_archive(archive_path: str = None) -> str:
    """Find all pyproject.toml / scripts etc.. and create a tar archive preserving structure."""
    repo_path = resolve_repo_path()
    archive_path = os.path.join(f"{repo_path}/dockerfiles/poetry", DEFAULT_E2E_DOCKER_ESSENTIAL_FILES_ARCHIVE_NAME)

    essentials = get_e2e_docker_essentials_files_paths()
    # Add makefile and other essentials files so the make dev-mode will work
    with tarfile.open(archive_path, "w:gz") as tar:
        # Add monorepo and runtime pyproject.toml files
        for pyproject_file in essentials:
            if os.path.exists(pyproject_file):
                tar.add(pyproject_file, arcname=os.path.relpath(pyproject_file, repo_path))
    return archive_path


def _maybe_build_image(image_name: str, image_path: str):
    # Use sh -c is required since the command includes pipes (|) and multiple commands.
    images_find_cmd = [
        "sh",
        "-c",
        'docker images --format "{{.Repository}} {{.Tag}} {{.ID}}" | grep '
        + image_name
        + " | sort -Vk2 | tail -n 1 | awk '{print $3}'",
    ]
    exit_code, output = run(images_find_cmd)

    if exit_code == 0:
        image_id = output.strip()
        force_build = should_build_image_before_tests()
        if image_id and not force_build:
            print(f"\n✅ Image {image_name} already exists, skipping build...")
            return
        else:
            print("\n🔨 Building Docker image for E2E tests...\n")
            print(f"  🛠️ Dockerfile Path: {image_path}")
            print(f"  📂 Build Context: {os.path.dirname(image_path)}")

            archive_path = create_project_essentials_archive()
            print(f"  🗃️ Created archive: {archive_path}\n")

            build_cmd = ["docker", "build", "-f", image_path, "-t", image_name, os.path.dirname(image_path)]
            exit_code, output = run(build_cmd, is_build=True)
            if exit_code == 0:
                print(f"\n✅ Image {image_name} built successfully!")
            else:
                print(f"\n❌ Error building image: {output}")
                sys.exit(1)
    else:
        print(f"\n❌ Error finding image: {output}")
        sys.exit(1)


def run_tests_in_container(test_path=None, only_e2e=True, report=False):
    _maybe_build_image(DEFAULT_POETRY_IMAGE_NAME, DEFAULT_POETRY_DOCKERFILE_FILE_PATH)
    _run_docker_container(DEFAULT_POETRY_IMAGE_NAME, test_path, only_e2e, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests in a Docker container.")
    parser.add_argument("--test-path", type=str, help="Path to the test file or directory", default=None)
    parser.add_argument("--only-e2e", action="store_true", help="Run only E2E tests (default: False)", default=False)
    parser.add_argument("--report", action="store_true", help="Generate coverage HTML report", default=False)

    args = parser.parse_args()
    run_tests_in_container(test_path=args.test_path, only_e2e=args.only_e2e, report=args.report)


# def _test_file_to_docker_path(host_test_file_abs_path: str) -> str:
#     """Remove the last 'provisioner' directory from the path and return the relative path."""
#     parts = host_test_file_abs_path.split("/")

#     for i in range(len(parts) - 1, -1, -1):  # Iterate from right to left
#         if parts[i] == "provisioner":  # Found a 'provisioner' directory
#             return "/".join(parts[i + 1 :])  # Return everything after this 'provisioner'

#     return host_test_file_abs_path  # If no 'provisioner' found, return the original path
