#!/usr/bin/env python3

import argparse
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import List, Optional, Set, Tuple

import tomllib

# Docker-related constants
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.resolve())
DEFAULT_POETRY_DOCKER_FOLDER_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/poetry"
DEFAULT_POETRY_DOCKERFILE_FILE_PATH = f"{DEFAULT_POETRY_DOCKER_FOLDER_PATH}/Dockerfile"
DEFAULT_POETRY_HASH_FILE = f"{DEFAULT_POETRY_DOCKER_FOLDER_PATH}/.dockerfile_hash"
DEFAULT_POETRY_BUILT_SDIST_FOLDER = f"{DEFAULT_POETRY_DOCKER_FOLDER_PATH}/dists/"
DEFAULT_CONTAINER_PROJECT_PATH = "/app"
DEFAULT_POETRY_IMAGE_NAME = "provisioner-poetry-e2e"
DEFAULT_POETRY_TAGGED_IMAGE_NAME = "provisioner-poetry-e2e:latest"
DEFAULT_E2E_DOCKER_ESSENTIAL_FILES_ARCHIVE_NAME = "e2e_docker_essential_files.tar.gz"


def get_project_from_test_path(test_path: str) -> str:
    """Extract project name from test path."""
    # Remove any test class and method specifications from the path
    if "::" in test_path:
        test_path = test_path.split("::")[0]

    path = Path(test_path)
    if path.name == "plugins":
        # If the path is just "plugins", return all plugin projects
        plugins_dir = Path("plugins")
        if plugins_dir.exists():
            plugin_projects = [
                d.name for d in plugins_dir.iterdir() if d.is_dir() and d.name.startswith("provisioner_")
            ]
            return " ".join(plugin_projects)
    elif "plugins" in path.parts:
        # For plugin tests, return the plugin name
        plugin_parts = [part for part in path.parts if "provisioner_" in part]
        plugin_name = plugin_parts[0] if plugin_parts else "provisioner_shared"
        return plugin_name.removesuffix(".py") if plugin_name.endswith(".py") else plugin_name
    elif "runtime" in path.parts:
        return "provisioner"
    else:
        return "provisioner_shared"


def get_project_path(project: str) -> Path:
    """Get the path to a project's directory."""
    if project.endswith("_plugin"):
        return Path("plugins") / project
    else:
        return Path(project)


def get_dependencies(project: str) -> Set[str]:
    """Get dependencies for a project from pyproject.toml."""
    deps = {project}
    project_path = get_project_path(project)
    pyproject_path = project_path / "pyproject.toml"

    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})

        for dep in dependencies:
            if dep.startswith("provisioner_"):
                deps.add(dep)
                deps.update(get_dependencies(dep))

        return deps
    except FileNotFoundError:
        print(f"Warning: No pyproject.toml found for {project} at {pyproject_path}")
        return deps
    except Exception as e:
        print(f"Error reading dependencies for {project}: {e}")
        return deps


def build_sdists(projects: Set[str]):
    """Build sdist packages for specified projects and install them in the venv."""
    output_dir = Path(DEFAULT_POETRY_BUILT_SDIST_FOLDER)
    output_dir.mkdir(parents=True, exist_ok=True)

    for file in output_dir.glob("*.tar.gz"):
        file.unlink()

    print("Building sdist packages for:")
    for project in projects:
        print(f"  - {project}")

    for project in projects:
        project_path = get_project_path(project)
        dist_dir = project_path / "dist"

        try:
            # Create a temporary MANIFEST.in file to exclude test files
            manifest_path = project_path / "MANIFEST.in"
            with open(manifest_path, "w") as f:
                f.write("exclude */*_test.py\n")
                f.write("exclude */*_test/*\n")
                f.write("exclude *_test.py\n")
                f.write("exclude *_test/*\n")

            subprocess.run(
                # ["poetry", "build-project", "--format", "sdist"],
                ["poetry", "build", "--format", "sdist"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"Built {project} sdist package")

            for sdist in dist_dir.glob("*.tar.gz"):
                shutil.copy2(sdist, output_dir / sdist.name)
                print(f"Copied {sdist.name} to {output_dir}")

            shutil.rmtree(dist_dir)
            manifest_path.unlink()  # Remove the temporary MANIFEST.in file

        except subprocess.CalledProcessError as e:
            print(f"❌ Error building {project}: {e.stderr}")
            print("   This might indicate missing dependencies or manifest.json files.")
            print(f"   Try running 'poetry install' in the {project} directory.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error processing {project}: {str(e)}")
            sys.exit(1)


def check_venv_health():
    """Check for common virtual environment issues that might cause pip failures."""
    try:
        # Check if there are any stale executable files that might cause issues
        result = subprocess.run(
            ["poetry", "run", "python", "-c", "import sys; print(sys.executable)"], capture_output=True, text=True
        )
        if result.returncode == 0:
            venv_bin_dir = Path(result.stdout.strip()).parent

            # Look for common problematic files
            problematic_files = ["test_runner", "pytest_runner"]
            found_issues = []

            for file in problematic_files:
                file_path = venv_bin_dir / file
                if file_path.exists():
                    found_issues.append(str(file_path))

            if found_issues:
                print("⚠️  Warning: Found potentially problematic files in virtual environment:")
                for issue in found_issues:
                    print(f"   - {issue}")
                print("   These files might cause pip uninstall failures.")
                print("   Consider running 'make clear-project' if you encounter issues.")

    except Exception:
        # Silently ignore venv health check failures
        pass


def install_sdists():
    """Install built sdist packages into the project's virtual environment."""
    output_dir = Path(DEFAULT_POETRY_BUILT_SDIST_FOLDER)
    if not output_dir.exists():
        print("No sdist packages found to install")
        return

    # Check virtual environment health
    check_venv_health()

    print("Installing sdist packages:")

    # Get package names to uninstall
    package_names = [p.stem.split("-")[0] for p in output_dir.glob("*.tar.gz")]

    # Uninstall existing packages (ignore errors for packages that don't exist or have issues)
    print("Uninstalling existing packages from local virtual environment...")
    for package_name in package_names:
        try:
            result = subprocess.run(
                ["poetry", "run", "pip", "uninstall", package_name, "-y"],
                capture_output=True,
                text=True,
                timeout=30,  # Add timeout to prevent hanging
            )
            if result.returncode == 0:
                print(f"  - Successfully uninstalled {package_name}")
            else:
                print(f"  - {package_name} was not installed or already removed")
        except subprocess.TimeoutExpired:
            print(f"  - Timeout uninstalling {package_name}, skipping...")
        except subprocess.CalledProcessError:
            print(f"  - Failed to uninstall {package_name}, skipping...")
        except Exception as e:
            print(f"  - Error uninstalling {package_name}: {str(e)}, skipping...")

    # Install new packages
    try:
        for sdist in output_dir.glob("*.tar.gz"):
            print(f"  - Installing {sdist.name}")
            subprocess.run(
                ["poetry", "run", "pip", "install", str(sdist.absolute()), "--no-deps"],
                check=True,
                capture_output=True,
                text=True,
            )
        print("All sdist packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e.stderr}")
        print("This might indicate a dependency issue or corrupted package.")
        print("Try running 'make clear-project' and rebuilding.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during installation: {str(e)}")
        sys.exit(1)


def clean_pycache_directories():
    """Clean up all __pycache__ directories in the project."""
    print("Cleaning project from __pycache__ folders ...")
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            # print(f"Cleaning {pycache_path}")
            shutil.rmtree(pycache_path)
            dirs.remove("__pycache__")


def get_test_directories() -> List[str]:
    """Get all directories containing test files in the project."""
    test_dirs = set()

    # Add main project directories
    for project in ["provisioner_shared", "provisioner"]:
        project_path = Path(project)
        if project_path.exists():
            test_dirs.add(str(project_path))

    # Add plugin directories
    plugins_dir = Path("plugins")
    if plugins_dir.exists():
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir.name.startswith("provisioner_"):
                test_dirs.add(str(plugin_dir))

    return list(test_dirs)


def run_local_tests(test_path: str = None, report_type: str = None, only_e2e: bool = False, skip_e2e: bool = False):
    """Run tests locally using pytest and coverage."""
    # Clean up __pycache__ directories
    clean_pycache_directories()

    # Create a new environment with existing env vars plus our additions
    env = os.environ.copy()
    env.update(
        {
            "COLUMNS": "200",
            "PYTHONIOENCODING": "utf-8",
            "PYTEST_ADDOPTS": "--tb=short --no-header --import-mode=importlib --ignore=.venv",
        }
    )

    cmd = ["poetry", "run", "coverage", "run", "-m", "pytest"]

    if test_path:
        cmd.append(test_path)
    else:
        # Add all project directories containing test files
        cmd.extend(get_test_directories())

    # Add e2e flags
    if only_e2e:
        cmd.append("--only-e2e")
    elif skip_e2e:
        cmd.append("--skip-e2e")

    try:
        subprocess.run(cmd, check=True, env=env)
        # Generate coverage report if requested
        if report_type:
            subprocess.run(["poetry", "run", "coverage", "report"], check=True)
            if report_type == "html":
                subprocess.run(["poetry", "run", "coverage", "html"], check=True)
                print(f"\n✅ HTML coverage report generated in {os.getcwd()}/htmlcov/index.html")
            elif report_type == "xml":
                subprocess.run(["poetry", "run", "coverage", "xml"], check=True)
                print("\n✅ XML coverage report generated in coverage.xml")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


# Docker-related functions
def get_project_mounted_volumes() -> List[str]:
    return [
        "dockerfiles",
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


def resolve_repo_path():
    """Resolve the absolute path of the repository."""
    current_dir = os.path.abspath(os.getcwd())
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, ".git")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise RuntimeError("Repository root not found.")


def get_test_container_volumes(project_root: str) -> List[str]:
    folders_to_mount = get_project_mounted_volumes()
    return [f"{os.path.join(project_root, folder)}:/app/{folder}" for folder in folders_to_mount]


def run_docker_command(cmd: List[str], is_build: bool = False) -> Tuple[int, str]:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    output_lines = []
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


def create_project_essentials_archive() -> str:
    """Create archive with essential project files."""
    repo_path = resolve_repo_path()
    archive_path = os.path.join(f"{repo_path}/dockerfiles/poetry", DEFAULT_E2E_DOCKER_ESSENTIAL_FILES_ARCHIVE_NAME)

    essentials = [
        os.path.join(repo_path, "pyproject.toml"),
        os.path.join(repo_path, "poetry.toml"),
        os.path.join(repo_path, "Makefile"),
        os.path.join(repo_path, "scripts"),
    ]

    with tarfile.open(archive_path, "w:gz") as tar:
        for essential_file in essentials:
            if os.path.exists(essential_file):
                tar.add(essential_file, arcname=os.path.relpath(essential_file, repo_path))
    return archive_path


def get_dockerfile_hash(dockerfile_path):
    """Calculate hash of Dockerfile content"""
    if not os.path.exists(dockerfile_path):
        print(f"Warning: Dockerfile not found at {dockerfile_path}")
        return "no-dockerfile-found"

    with open(dockerfile_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def has_dockerfile_hash_changed(current_hash, hash_file_path):
    """Check if Dockerfile hash has changed compared to stored hash"""
    # If hash file doesn't exist, consider it as changed
    if not os.path.exists(hash_file_path):
        return True

    with open(hash_file_path, "r") as f:
        stored_hash = f.read().strip()

    return stored_hash != current_hash


def save_dockerfile_hash(hash_value, hash_file_path):
    """Save Dockerfile hash for future comparison"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(hash_file_path), exist_ok=True)

    with open(hash_file_path, "w") as f:
        f.write(hash_value)


def build_docker_image(image_name: str, image_path: str):
    """Build Docker image if needed using content hash for caching."""
    # Check if CI has pre-built the image (for GitHub Actions optimization)
    if os.getenv("CI_PREBUILT_DOCKER_IMAGES") == "true":
        print(f"✅ Skipping build for {image_name} - using CI pre-built image")
        return

    # Check if image exists
    images_find_cmd = [
        "sh",
        "-c",
        f"docker images --format \"{{{{.Repository}}}} {{{{.Tag}}}} {{{{.ID}}}}\" | grep {image_name} | sort -Vk2 | tail -n 1 | awk '{{print $3}}'",
    ]
    exit_code, output = run_docker_command(images_find_cmd)
    image_exists = exit_code == 0 and output.strip()

    # Calculate Dockerfile hash
    dockerfile_hash = get_dockerfile_hash(image_path)
    print(f"Image {image_name} Dockerfile hash: {dockerfile_hash}")

    # Define hash file path
    hash_file_path = os.path.join(os.path.dirname(image_path), ".dockerfile_hash")

    # Check if hash has changed
    hash_changed = has_dockerfile_hash_changed(dockerfile_hash, hash_file_path)

    if image_exists and not hash_changed:
        print(f"\n✅ Image {image_name} already exists with current Dockerfile hash, skipping build...")
        return
    else:
        if hash_changed:
            print("Dockerfile has changed since last build, rebuilding image...")
        else:
            print("Image doesn't exist, building it...")

        print("\n  🔨 Building Docker image for tests...")
        archive_path = create_project_essentials_archive()
        print(f"  🗃️ Created archive: {archive_path}\n")

        build_cmd = ["docker", "build", "-f", image_path, "-t", image_name, os.path.dirname(image_path)]
        exit_code, output = run_docker_command(build_cmd, is_build=True)

        if exit_code == 0:
            print(f"\n✅ Image {image_name} built successfully!")
            # Save the new hash after successful build
            save_dockerfile_hash(dockerfile_hash, hash_file_path)
        else:
            print(f"\n❌ Error building image: {output}")
            sys.exit(1)


def run_docker_tests(
    test_path: Optional[str] = None, only_e2e: bool = True, report_type: str = None, skip_e2e: bool = False
):
    """Run tests in Docker container."""
    build_docker_image(DEFAULT_POETRY_IMAGE_NAME, DEFAULT_POETRY_DOCKERFILE_FILE_PATH)

    project_root = resolve_repo_path()
    mount_vols = get_test_container_volumes(project_root)
    vol_list = []
    for vol in mount_vols:
        vol_list.extend(["-v", vol])

    # Set environment variables for the container
    env_vars = [
        "-e",
        "COLUMNS=200",
        "-e",
        "PYTHONIOENCODING=utf-8",
        "-e",
        "PYTEST_ADDOPTS=--tb=short --no-header --import-mode=importlib",
    ]

    if report_type:
        env_vars.extend(["-e", f"COVERAGE_REPORT_TYPE={report_type}"])

    cmd = [
        "docker",
        "run",
        "--network=host",
        "--rm",
        "-i",
        "--tty=false",
        # "-it",
        "--name",
        DEFAULT_POETRY_IMAGE_NAME,
        "-v",
        f"{project_root}/dockerfiles/poetry/dists:/tmp/provisioner-sdists",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        *env_vars,  # Add environment variables
        *vol_list,
        "-w",
        "/app",
        DEFAULT_POETRY_IMAGE_NAME,
    ]

    if test_path:
        cmd.append(test_path)
        print(f"\n🧪 Running test: {test_path}\n")
    else:
        print("\n🧪 Running tests suite...\n")

    # Pass both flags independently
    if only_e2e:
        cmd.append("--only-e2e")
    elif skip_e2e:
        cmd.append("--skip-e2e")

    exit_code, output = run_docker_command(cmd)
    if exit_code == 0:
        print(output)
        print(f"\n✅ Test run on image {DEFAULT_POETRY_IMAGE_NAME} executed successfully!")
    else:
        print(f"\n❌ Test run failed on image: {DEFAULT_POETRY_IMAGE_NAME}, output: {output}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run provisioner tests locally or in Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run specific test locally
  ./run_tests.py path/to/test.py

  # Run all tests locally
  ./run_tests.py --all

  # Run specific test in container
  ./run_tests.py path/to/test.py --container

  # Run all tests ignoring E2E tests
  ./run_tests.py --all --skip-e2e

  # Run all tests in container with E2E only and HTML coverage report
  ./run_tests.py --all --container --only-e2e --report html

  # Run tests with XML coverage report
  ./run_tests.py --all --report xml

  # Run tests without coverage report
  ./run_tests.py --all
""",
    )
    parser.add_argument("test_path", nargs="?", help="Path to specific test file")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--container", action="store_true", help="Run tests in Docker container")
    parser.add_argument("--only-e2e", action="store_true", help="Run only E2E tests")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    parser.add_argument(
        "--report",
        nargs="?",
        choices=["html", "xml"],
        const="html",  # Default value when --report is used without argument
        help="Generate coverage report in specified format (html or xml). If no format is specified, defaults to html.",
    )
    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Ensure either test_path or --all is provided
    if not args.test_path and not args.all:
        parser.error("Either a test path or --all must be specified")
        sys.exit(1)

    # Ensure test_path and --all are not used together
    if args.test_path and args.all:
        parser.error("Cannot specify both test path and --all")
        sys.exit(1)

    # Ensure --only-e2e and --skip-e2e are not used together
    if args.only_e2e and args.skip_e2e:
        parser.error("Cannot specify both --only-e2e and --skip-e2e")
        sys.exit(1)

    if args.test_path:
        project = get_project_from_test_path(args.test_path)
        # Split project string into list if it contains multiple projects
        projects_to_build = set()
        for p in project.split():
            projects_to_build.add(p)
            projects_to_build.update(get_dependencies(p))
        print(f"Building packages for test: {args.test_path}")
    elif args.all:
        projects_to_build = {
            "provisioner_shared",
            "provisioner",
            *[d.name for d in Path("plugins").iterdir() if d.is_dir() and d.name.startswith("provisioner_")],
        }
        print("Building all packages")

    build_sdists(projects_to_build)

    if args.container:
        run_docker_tests(args.test_path, args.only_e2e, args.report, args.skip_e2e)
    else:
        # For local tests, uninstall existing packages before installing sdists
        print("\nUninstalling existing packages from local virtual environment...")
        subprocess.run(
            ["poetry", "run", "pip", "uninstall", "-y", "provisioner", "provisioner_shared", "provisioner_*_plugin"],
            check=False,  # Don't fail if some packages aren't installed
            capture_output=True,
            text=True,
        )
        install_sdists()
        run_local_tests(args.test_path, args.report, args.only_e2e, args.skip_e2e)


if __name__ == "__main__":
    main()
