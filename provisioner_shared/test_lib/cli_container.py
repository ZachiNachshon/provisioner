#!/usr/bin/env python3

import hashlib
import json
import os
import pathlib
import time
from typing import Dict, List

import docker
import paramiko
from testcontainers.core.container import DockerContainer

DEFAULT_REMOTE_SSH_IMAGE_NAME = "provisioner-remote-ssh-e2e"

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.resolve())
DEFAULT_REMOTE_SSH_DOCKERFILE_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/remote_ssh/Dockerfile"
DEFAULT_REMOTE_SSH_HASH_FILE = f"{PROJECT_ROOT_PATH}/dockerfiles/remote_ssh/.dockerfile_hash"


#
# To debug the container, run the following command:
#  docker run -v ~/.ssh:/root/.ssh -p 2222:22 -d -it --name "z-provisioner-remote-ssh-e2e" "provisioner-remote-ssh-e2e"
#
class RemoteSSHContainer(DockerContainer):
    def __init__(
        self,
        image="provisioner-remote-ssh-e2e",
        custom_flags: List[str] = None,
        network_name: str = None,
        ports: Dict[int, int] = None,
    ):
        super().__init__(image)
        self.with_exposed_ports(22)  # Ensure SSH is exposed

        # Store port mappings (container_port -> host_port)
        self.ports = ports or {}
        # Add any ports from the dictionary to exposed ports
        for container_port in self.ports.keys():
            self.with_exposed_ports(container_port)

        self.custom_flags = custom_flags or []
        self.maybe_network_name = network_name
        self.network_created = False
        self.docker_client = docker.from_env()
        self.network = None
        self.container_options = {}

    def start(self, ssh_port: int = 2222):
        # Build the Docker image first
        self.build_image()

        # Create network if it doesn't exist
        if self.maybe_network_name:
            self._ensure_network_exists()

        # Apply custom flags
        self._apply_custom_flags()

        # Connect to the network
        if self.maybe_network_name and self.network:
            self.with_network(self.network)

        # Bind SSH port
        self.with_bind_ports(22, ssh_port)

        # Bind additional ports if specified
        for container_port, host_port in self.ports.items():
            self.with_bind_ports(container_port, host_port)

        # Apply container options before starting
        if self.container_options:
            for key, value in self.container_options.items():
                setattr(self, key, value)

        super().start()
        time.sleep(3)  # Give SSH time to initialize

        # Get dynamically assigned port
        self.ssh_port = self.get_exposed_port(22)
        print(f"SSH Running on 127.0.0.1:{self.ssh_port}")

        # Wait for SSH to be responsive
        self._wait_for_ssh()
        return self

    def _apply_custom_flags(self):
        """Apply custom Docker flags to container options"""
        for flag in self.custom_flags:
            if flag.startswith("--"):
                # Remove the leading '--' from the flag
                flag_name = flag[2:]

                # Convert flag to container option
                # For boolean flags (no value), set to True
                # For flags with values, they should be passed as --flag=value
                if "=" in flag_name:
                    # Handle flags with values
                    key, value = flag_name.split("=", 1)
                    self.container_options[key] = value
                else:
                    # Handle boolean flags
                    self.container_options[flag_name] = True

    def stop(self):
        """Stop the container and clean up resources"""
        super().stop()
        # Clean up network if we created it
        if self.network_created and self.network:
            try:
                self.network.remove()
                print(f"Removed network: {self.maybe_network_name}")
            except docker.errors.NotFound:
                # Network already removed
                pass
            except Exception as e:
                print(f"Warning: Failed to remove network {self.maybe_network_name}: {str(e)}")

    def _ensure_network_exists(self):
        """Create the network if it doesn't exist"""
        try:
            # Check if network exists
            self.network = self.docker_client.networks.get(self.maybe_network_name)
            print(f"Network {self.maybe_network_name} already exists")
        except docker.errors.NotFound:
            # Network doesn't exist, create it
            self.network = self.docker_client.networks.create(self.maybe_network_name, driver="bridge")
            self.network_created = True
            print(f"Created network: {self.maybe_network_name}")
        except Exception as e:
            print(f"Warning: Failed to check/create network {self.maybe_network_name}: {str(e)}")

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
        """Build the Docker image locally using Dockerfile content hash for caching"""
        client = docker.from_env()
        image_exist = self._image_exists(client, DEFAULT_REMOTE_SSH_IMAGE_NAME)

        # Calculate Dockerfile hash
        dockerfile_hash = self._get_dockerfile_hash(DEFAULT_REMOTE_SSH_DOCKERFILE_PATH)
        print(f"Image {DEFAULT_REMOTE_SSH_IMAGE_NAME} Dockerfile hash: {dockerfile_hash}")

        # Check if hash has changed
        hash_changed = self._has_dockerfile_hash_changed(dockerfile_hash, DEFAULT_REMOTE_SSH_HASH_FILE)

        if image_exist and not hash_changed:
            print(
                f"Image {DEFAULT_REMOTE_SSH_IMAGE_NAME} already exists with current Dockerfile hash, skipping build..."
            )
            return
        else:
            if hash_changed:
                print("Dockerfile has changed since last build, rebuilding image...")
            else:
                print("Image doesn't exist, building it...")

            print("\nBuilding Docker image for E2E tests...")
            print(f"Dockerfile Path: {DEFAULT_REMOTE_SSH_DOCKERFILE_PATH}")
            print(f"Build Context: {PROJECT_ROOT_PATH}\n")
            try:
                # Build the image
                build_logs = client.api.build(
                    path=PROJECT_ROOT_PATH,
                    dockerfile=DEFAULT_REMOTE_SSH_DOCKERFILE_PATH,
                    tag=DEFAULT_REMOTE_SSH_IMAGE_NAME,
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
                self._save_dockerfile_hash(dockerfile_hash, DEFAULT_REMOTE_SSH_HASH_FILE)

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

    def get_ssh_port(self):
        return self.get_exposed_port(22)

    def get_port(self, container_port):
        """
        Get the host port that maps to the specified container port.

        Args:
            container_port: The container port to get the mapping for

        Returns:
            The host port mapped to the container port
        """
        return self.get_exposed_port(container_port)

    def get_container_id(self):
        """
        Get the ID of the container.

        Returns:
            str: The ID of the container
        """
        return self.get_wrapped_container().id

    def exec_run(self, cmd, detach=False):
        """
        Execute a command in the container.

        Args:
            cmd: The command to run
            detach: Whether to run the command in detached mode

        Returns:
            The result of the command
        """
        container = self.get_wrapped_container()
        exec_id = self.docker_client.api.exec_create(container.id, cmd)["Id"]

        if detach:
            self.docker_client.api.exec_start(exec_id, detach=True)
            return type("ExecResult", (), {"exit_code": 0, "output": b""})
        else:
            output = self.docker_client.api.exec_start(exec_id)
            exit_code = self.docker_client.api.exec_inspect(exec_id)["ExitCode"]
            return type("ExecResult", (), {"exit_code": exit_code, "output": output})
