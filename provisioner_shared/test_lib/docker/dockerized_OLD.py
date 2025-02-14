import inspect
import json
import os
import pathlib
import sys
from enum import Enum
from typing import Optional

import docker


class DockerImage(str, Enum):
    RemoteSSH = "RemoteSSH"
    Poetry = "Poetry"
    RaspbianOS = "RaspbianOS"


def test_file_to_docker_path(host_test_file_abs_path: str) -> str:
    """Iterate over the test file path and extract only the relative project path."""
    parts = host_test_file_abs_path.split("/")
    for i in range(len(parts) - 1, -1, -1):  # Iterate from right to left
        if parts[i] == "provisioner":
            # Check if there are any more 'provisioner' directories after this one
            if "provisioner" not in parts[i + 1 :]:
                return "/".join(parts[i:])
    return host_test_file_abs_path


DEFAULT_REMOTE_SSH_IMAGE_NAME = "provisioner-remote-ssh-e2e:latest"
DEFAULT_POETRY_IMAGE_NAME = "provisioner-poetry-e2e:latest"
RASPBIAN_OS_IMAGE_NAME = "raspbian-os:latest"

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.parent.parent.parent.resolve())
TEST_DOCKER_ROOT_PATH = str(pathlib.Path(__file__).parent.resolve())
DEFAULT_REMOTE_SSH_DOCKERFILE_PATH = f"{TEST_DOCKER_ROOT_PATH}/python/Dockerfile"
DEFAULT_POETRY_DOCKERFILE_PATH = f"{TEST_DOCKER_ROOT_PATH}/poetry/Dockerfile"
RASPBIAN_OS_DOCKERFILE_PATH = f"{TEST_DOCKER_ROOT_PATH}/raspbian_os/Dockerfile"


def dockerized(image: DockerImage = DockerImage.Poetry):
    """Decorator to run the test inside a Docker container if not already in one."""

    image_name = ""
    image_path = ""
    match image:
        case DockerImage.RemoteSSH:
            image_name = DEFAULT_REMOTE_SSH_IMAGE_NAME
            image_path = DEFAULT_REMOTE_SSH_DOCKERFILE_PATH
        case DockerImage.Poetry:
            image_name = DEFAULT_POETRY_IMAGE_NAME
            image_path = DEFAULT_POETRY_DOCKERFILE_PATH
        case DockerImage.RaspbianOS:
            image_name = RASPBIAN_OS_IMAGE_NAME
            image_path = RASPBIAN_OS_DOCKERFILE_PATH
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
            print(f"📂 Build Context: {TEST_DOCKER_ROOT_PATH}")

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

            # Step 2: Define the test command inside the container
            test_command = ["poetry", "run", "coverage", "run", "-m", "pytest", test_file_in_docker]
            print(f"\n🧪 Running tests with command: {' '.join(test_command)}\n")

            container: Optional[docker.models.containers.Container] = None
            try:
                # Step 3: Run tests inside Docker with stream=True
                container = client.containers.run(
                    image_name,
                    command=test_command,
                    stdout=True,
                    stderr=True,
                    detach=True,
                    tty=True,  # Allocate a pseudo-TTY
                    remove=True,  # Auto-remove container when finished
                )

                # Step 4: Stream logs in real-time
                for log in container.logs(stream=True, follow=True):
                    print(log.decode("utf-8"), end="")

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
