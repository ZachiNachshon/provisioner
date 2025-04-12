#!/usr/bin/env python3

import hashlib
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
DEFAULT_RPI_OS_HASH_FILE = f"{PROJECT_ROOT_PATH}/dockerfiles/raspbian_os/.dockerfile_hash"

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
        """Build the Docker image locally using Dockerfile content hash for caching."""
        client = docker.from_env()
        image_exist = self._image_exists(client, DEFAULT_RPI_OS_IMAGE_NAME)

        # Calculate Dockerfile hash
        dockerfile_hash = self._get_dockerfile_hash(DEFAULT_RPI_OS_DOCKERFILE_PATH)
        print(f"Image {DEFAULT_RPI_OS_IMAGE_NAME} Dockerfile hash: {dockerfile_hash}")

        # Check if hash has changed
        hash_changed = self._has_dockerfile_hash_changed(dockerfile_hash, DEFAULT_RPI_OS_HASH_FILE)

        if image_exist and not hash_changed:
            print(f"Image {DEFAULT_RPI_OS_IMAGE_NAME} already exists with current Dockerfile hash, skipping build...")
            return
        else:
            if hash_changed:
                print("Dockerfile has changed since last build, rebuilding image...")
            else:
                print("Image doesn't exist, building it...")

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

                # Save the new hash after successful build
                self._save_dockerfile_hash(dockerfile_hash, DEFAULT_RPI_OS_HASH_FILE)

            except Exception as e:
                print(f"Failed to build Docker image: {str(e)}")
                raise RuntimeError(f"Failed to build Docker image: {str(e)}")

    def _get_dockerfile_hash(self, dockerfile_path):
        """Calculate hash of Dockerfile content"""
        if not os.path.exists(dockerfile_path):
            print(f"Warning: Dockerfile not found at {dockerfile_path}")
            return "no-dockerfile-found"

        with open(dockerfile_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _has_dockerfile_hash_changed(self, current_hash, hash_file_path):
        """Check if Dockerfile hash has changed compared to stored hash"""
        # If hash file doesn't exist, consider it as changed
        if not os.path.exists(hash_file_path):
            return True

        with open(hash_file_path, "r") as f:
            stored_hash = f.read().strip()

        return stored_hash != current_hash

    def _save_dockerfile_hash(self, hash_value, hash_file_path):
        """Save Dockerfile hash for future comparison"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(hash_file_path), exist_ok=True)

        with open(hash_file_path, "w") as f:
            f.write(hash_value)

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
