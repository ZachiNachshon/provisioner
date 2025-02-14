import inspect
import json
import os
import pathlib
import sys
from enum import Enum
from typing import Optional

import docker

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.parent.resolve())
DEFAULT_POETRY_DOCKERFILE_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/poetry/Dockerfile"

DEFAULT_POETRY_IMAGE_NAME = "provisioner-poetry-e2e:latest"


class DockerImage(str, Enum):
    Poetry = "Poetry"

def test_file_to_docker_path(host_test_file_abs_path: str) -> str:
    """Remove the last 'provisioner' directory from the path and return the relative path."""
    parts = host_test_file_abs_path.split("/")

    for i in range(len(parts) - 1, -1, -1):  # Iterate from right to left
        if parts[i] == "provisioner":  # Found a 'provisioner' directory
            return "/".join(parts[i + 1 :])  # Return everything after this 'provisioner'

    return host_test_file_abs_path  # If no 'provisioner' found, return the original path


def image_exists(client: docker.DockerClient, image_name: str) -> bool:
    """Check if a Docker image exists locally."""
    try:
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False


def maybe_build_image(client, image_name: str, image_path: str, force_build: bool):
    # Check if image already exists
    if image_exists(client, image_name) and force_build is False:
        print(f"\n✅ Image {image_name} already exists, skipping build...")
    else:
        # Step 1: Build the Docker image
        print("\n🔨 Building Docker image for E2E tests...\n")
        try:
            build_logs = client.api.build(path=PROJECT_ROOT_PATH, dockerfile=image_path, tag=image_name, rm=True)

            # Stream build logs
            for log in build_logs:
                try:
                    log_line = json.loads(log.decode("utf-8"))
                    if "stream" in log_line:
                        print(log_line["stream"].strip())
                except json.JSONDecodeError:
                    print(log.decode("utf-8").strip())

        except docker.errors.BuildError as e:
            print(f"\n❌ BuildError: {e.msg}")
            raise
        except Exception as e:
            print(f"\n❌ Unexpected error during build: {e}")
            raise


def dockerized(image: DockerImage = DockerImage.Poetry, force_build: bool = False):
    """Decorator to run the test inside a Docker container if not already in one."""

    image_name = ""
    image_path = ""
    match image:
        case DockerImage.Poetry:
            image_name = DEFAULT_POETRY_IMAGE_NAME
            image_path = DEFAULT_POETRY_DOCKERFILE_PATH
        case _:
            raise ValueError(f"Unsupported Docker image: {image}")

    def decorator(test_func):
        if os.path.exists("/.dockerenv"):  # Detect if running inside a Docker container
            return test_func

        def wrapper(*args, **kwargs):
            print(f"\n🚀 Running {test_func.__name__} inside Docker...\n")
            client = docker.from_env()

            # Get the current test file path
            test_file = inspect.getfile(test_func)
            test_file_in_docker = test_file_to_docker_path(test_file)
            print(f"📄 Test file: {test_file_in_docker}")
            print(f"🛠️ Dockerfile Path: {image_path}")
            print(f"📂 Build Context: {os.path.dirname(DEFAULT_POETRY_DOCKERFILE_PATH)}")

            # Step 1: Build the Docker image
            maybe_build_image(client, image_name, image_path, force_build)

            # Step 2: Define the test command inside the container
            test_command = ["poetry", "run", "coverage", "run", "-m", "pytest", test_file_in_docker, "--e2e"]
            print(f"\n🧪 Running tests with command: {' '.join(test_command)}\n")

            container: Optional[docker.models.containers.Container] = None
            try:
                host_dir = os.getcwd()
                container_dir = "/home/testuser/app"
                custom_file = "pyproject.toml"  # File you want to override

                # Define the path for the .venv on the host and container
                host_venv_path = os.path.join(host_dir, ".venv")
                container_venv_path = os.path.join(container_dir, ".venv")

                # List of folders to mount (adjust as needed)
                folders_to_mount = [
                    ".venv/bin",
                    ".venv/lib",
                    "provisioner", 
                    "provisioner_shared", 
                    "plugins",
                    "scripts",
                    ".coveragerc",
                    "conftest.py",
                    "Makefile",
                    "pyproject.toml",
                    "poetry.lock",
                    "poetry.toml",
                    "pytest.ini"]
                
                # Define volumes without mounting `.venv`
                volumes = {
                    os.path.join(host_dir, folder): {
                        "bind": os.path.join(container_dir, folder),
                        "mode": "rw",
                    }
                    for folder in folders_to_mount
                }

                # Step 3: Run tests inside Docker with stream=True
                container = client.containers.run(
                    image_name,
                    command=test_command,
                    stdout=True,
                    stderr=True,
                    detach=True,
                    tty=True,  # Allocate a pseudo-TTY
                    remove=True,  # Auto-remove container when finished
                    volumes=volumes,
                    working_dir=container_dir,  # Set working directory inside the container
                    # environment={
                    #     "VIRTUAL_ENV": host_venv_path,
                    #     "POETRY_VIRTUALENVS_IN_PROJECT": "true",  # Force Poetry to use .venv inside container
                    # },
                )

                # Step 4: Stream logs in real-time
                for log in container.logs(stream=True, follow=True):
                    try:
                        print(log.decode("utf-8"), end="")
                    except UnicodeDecodeError:
                        print(f"[WARNING] Skipping non-UTF-8 log: {log}")

                # Step 5: Get final exit code
                result = container.wait(timeout=300)  # 5 minute timeout
                exit_code = result["StatusCode"]

                if exit_code != 0:
                    print(f"\n❌ Test failed with exit code {exit_code}")
                    sys.exit(exit_code)

                return test_func(*args, **kwargs)

            except docker.errors.ContainerError as e:
                print(f"\n❌ ContainerError: Command '{e.command}' failed with exit code {e.exit_status}")
                if container:
                    print("📝 Container Logs:")
                    print(container.logs().decode("utf-8"))
                raise

            except Exception as ex:
                print(f"\n❌ Unexpected error: {ex}")
                if container:
                    try:
                        container.kill()
                    except:
                        pass
                raise

            finally:
                # Ensure container cleanup
                if container:
                    try:
                        container.stop(timeout=5)
                    except:
                        pass

        return wrapper

    return decorator
