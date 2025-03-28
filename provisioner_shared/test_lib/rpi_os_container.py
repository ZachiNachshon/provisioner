#!/usr/bin/env python3

import json
import logging
import os
import pathlib
import time

import docker
import paramiko
from testcontainers.core.container import DockerContainer

DEFAULT_RPI_OS_IMAGE_NAME = "provisioner-rpi-os-e2e"

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.resolve())
DEFAULT_RPI_OS_DOCKERFILE_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/raspbian_os/Dockerfile"

logger = logging.getLogger(__name__)


class RemoteRPiOsContainer(DockerContainer):
    """A container class for testing Raspberry Pi OS configuration in a lightweight environment."""

    def __init__(self, image=DEFAULT_RPI_OS_IMAGE_NAME):
        # def __init__(self, timeout: int = 30):
        super().__init__(image)
        self.with_exposed_ports(22)  # Ensure SSH is exposed
        # self.timeout = timeout
        # self.ssh_port = None

    def start(self):
        """Start the container and wait for SSH to be ready."""
        # Build the Docker image first
        self.build_image()

        self.with_bind_ports(22, 2222)  # Bind port 22 to 2222
        # Start the container
        super().start()
        time.sleep(3)  # Give SSH time to initialize

        # Get dynamically assigned port
        self.ssh_port = self.get_exposed_port(22)
        print(f"SSH Running on 127.0.0.1:{self.ssh_port}")

        # Wait for SSH to be responsive
        self._wait_for_ssh()
        return self

    def _should_build_image_before_tests(self) -> bool:
        """Check if we should force rebuild the image before tests."""
        return os.getenv("PROVISIONER_BUILD_IMAGE_BEFORE_TESTS", "false").lower() == "true"

    def _wait_for_ssh(self):
        """Ensure SSH is ready before proceeding."""
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect("127.0.0.1", port=int(self.ssh_port), username="pi", password="raspberry")
                print("✅ SSH Connection Successful")
                client.close()
                return
            except Exception:
                print(f"🔄 Waiting for SSH... ({attempt + 1}/{max_attempts})")
                time.sleep(2)
                attempt += 1
        raise RuntimeError("❌ SSH did not start in time.")

    def _image_exists(self, client: docker.DockerClient, image_name: str) -> bool:
        """Check if a Docker image exists locally."""
        try:
            client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def build_image(self):
        """Build the Docker image locally."""
        client = docker.from_env()
        force_build = self._should_build_image_before_tests()
        image_exist = self._image_exists(client, DEFAULT_RPI_OS_IMAGE_NAME)

        if image_exist and not force_build:
            print(f"Image {DEFAULT_RPI_OS_IMAGE_NAME} already exists, skipping build...")
            return
        elif not image_exist or force_build:
            print("\nBuilding Docker image for E2E tests...")
            print(f"Dockerfile Path: {DEFAULT_RPI_OS_DOCKERFILE_PATH}")
            print(f"Build Context: {PROJECT_ROOT_PATH}\n")
            try:
                # Build the image
                build_logs = client.api.build(
                    path=PROJECT_ROOT_PATH,
                    dockerfile=DEFAULT_RPI_OS_DOCKERFILE_PATH,
                    tag=DEFAULT_RPI_OS_IMAGE_NAME,
                    rm=True,
                )

                # Stream build logs
                for log in build_logs:
                    try:
                        log_line = json.loads(log.decode("utf-8"))
                        if "stream" in log_line:
                            print(log_line["stream"].strip())
                    except json.JSONDecodeError:
                        print(log.decode("utf-8").strip())

            except Exception as e:
                print(f"Failed to build Docker image: {str(e)}")
                raise RuntimeError(f"Failed to build Docker image: {str(e)}")

    def get_ssh_port(self) -> int:
        """Get the exposed SSH port."""
        return int(self.ssh_port)

    # def get_ssh_user(self) -> str:
    #     """Get the SSH username."""
    #     return "pi"

    # def get_ssh_password(self) -> str:
    #     """Get the SSH password."""
    #     return "raspberry"

    # def get_container_logs(self) -> str:
    #     """Get the container logs."""
    #     return self.get_wrapped_container().logs().decode("utf-8")
