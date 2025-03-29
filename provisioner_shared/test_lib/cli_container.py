#!/usr/bin/env python3

import json
import os
import pathlib
import time
import hashlib

import docker
import paramiko
from testcontainers.core.container import DockerContainer

DEFAULT_REMOTE_SSH_IMAGE_NAME = "provisioner-remote-ssh-e2e"

# Define the root path of the project (absolute path)
PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.resolve())
# TEST_DOCKER_ROOT_PATH = str(pathlib.Path(__file__).parent.resolve())
DEFAULT_REMOTE_SSH_DOCKERFILE_PATH = f"{PROJECT_ROOT_PATH}/dockerfiles/remote_ssh/Dockerfile"
DEFAULT_REMOTE_SSH_HASH_FILE = f"{PROJECT_ROOT_PATH}/dockerfiles/remote_ssh/.dockerfile_hash"


#
# To debug the container, run the following command:
#  docker run -v ~/.ssh:/root/.ssh -p 2222:22 -d -it --name "z-provisioner-remote-ssh-e2e" "provisioner-remote-ssh-e2e"
#
class RemoteSSHContainer(DockerContainer):
    def __init__(self, image="provisioner-remote-ssh-e2e"):
        super().__init__(image)
        self.with_exposed_ports(22)  # Ensure SSH is exposed

    def start(self):
        # Build the Docker image first
        self.build_image()

        self.with_bind_ports(22, 2222)
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
        """Build the Docker image locally using Dockerfile content hash for caching"""
        client = docker.from_env()
        image_exist = self._image_exists(client, DEFAULT_REMOTE_SSH_IMAGE_NAME)
        
        # Calculate Dockerfile hash
        dockerfile_hash = self._get_dockerfile_hash(DEFAULT_REMOTE_SSH_DOCKERFILE_PATH)
        print(f"Image {DEFAULT_REMOTE_SSH_IMAGE_NAME} Dockerfile hash: {dockerfile_hash}")
        
        # Check if hash has changed
        hash_changed = self._has_dockerfile_hash_changed(dockerfile_hash, DEFAULT_REMOTE_SSH_HASH_FILE)
        
        if image_exist and not hash_changed:
            print(f"Image {DEFAULT_REMOTE_SSH_IMAGE_NAME} already exists with current Dockerfile hash, skipping build...")
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
            
        with open(dockerfile_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _has_dockerfile_hash_changed(self, current_hash, hash_file_path):
        """Check if Dockerfile hash has changed compared to stored hash"""
        # If hash file doesn't exist, consider it as changed
        if not os.path.exists(hash_file_path):
            return True
            
        with open(hash_file_path, 'r') as f:
            stored_hash = f.read().strip()
            
        return stored_hash != current_hash

    def _save_dockerfile_hash(self, hash_value, hash_file_path):
        """Save Dockerfile hash for future comparison"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(hash_file_path), exist_ok=True)
        
        with open(hash_file_path, 'w') as f:
            f.write(hash_value)


#     def __init__(self, core_cols: CoreCollaborators, allow_logging=False):
#         self.core_cols = core_cols
#         self.allow_logging = allow_logging
#         git_root_folder = self.find_git_root()

#         if not git_root_folder:
#             raise RuntimeError("No git root folder found")

#         # Build the Docker image first
#         self.build_image()

#         logger.info(f"Using remote SSH container from image: {DEFAULT_REMOTE_SSH_IMAGE_NAME}")

#         self.stop_existing_containers()

#         super().__init__(DEFAULT_REMOTE_SSH_IMAGE_NAME)
#         self._container = None  # Store container instance

#         self.disable_ryuk()
#         env_file_path = str(pathlib.Path(DEFAULT_REMOTE_SSH_DOCKERFILE_PATH).parent) + "/.env"
#         self._env_file_path = env_file_path  # Store for later use
#         self.copy_env_file(env_file_path)

#         env_file = self.load_env_file(env_file_path)
#         self.log_env_file(env_file)
#         # self.set_env_vars(env_file)
#         self.set_volume_mounts()
#         self.set_ports_mapping(env_file)
#         # self.set_network(env_file)

#     def find_git_root(self):
#         return self.core_cols.io_utils().find_git_repo_root_abs_path_fn(clazz=RemoteSSHContainer)

#     def _wait_until_started(self):

#         # Function to check if the port is open
#         def is_port_open():
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.settimeout(60)
#                 return s.connect_ex(("localhost", int(2222))) == 0

#         self.exec("service ssh status")

#         def stream_logs(container):
#             """ Continuously print logs from the container """
#             for line in container.get_wrapped_container().logs(stream=True, follow=True):
#                 print(line.decode("utf-8"), end="")  # Decode bytes to readable text

#         # Start a background thread to stream logs
#         log_thread = threading.Thread(target=stream_logs, args=(self,), daemon=True)
#         log_thread.start()

#         # Wait for SSH service to open the port (timeout set to 180 seconds)
#         wait_for(is_port_open)

#     def copy_env_file(self, env_file_path):
#         logger.info(f"Using .env file: {env_file_path}")
#         # Using volume mapping for the env file
#         self.with_volume_mapping(env_file_path, "/etc/provisioner/.env")
#         self.with_env("PROVISIONER_ENV_FILE", "/etc/provisioner/.env")

#     def start(self):
#         # Call parent's start method
#         container = super().start()
#         if not self._container:
#             raise RuntimeError("Container failed to start.")

#         # Setup environment after container starts
#         # self.setup_environment()

#         port = self.get_exposed_port(22)
#         print("================================")
#         print(f"Container exposed port: {port}")
#         print("================================")

#         container._wait_until_started()

#         return container

#     def stop_existing_containers(self):
#         client = docker.from_env()

#         # Find all running containers using this image
#         for container in client.containers.list(filters={"ancestor": DEFAULT_REMOTE_SSH_IMAGE_NAME}):
#             print(f"Stopping and removing container: {container.name}")
#             container.stop()
#             container.remove()

#     def setup_environment(self):
#         """Setup environment after container has started"""
#         if not hasattr(self, '_env_file_path'):
#             logger.warning("No env file path stored, skipping environment setup")
#             return

#         # Create directory and copy env file content
#         self.exec("mkdir -p /etc/provisioner")
#         with open(self._env_file_path, 'r') as f:
#             content = f.read()

#         # Escape single quotes in content
#         content = content.replace("'", "'\\''")
#         self.exec(f"echo '{content}' > /etc/provisioner/.env")
#         self.exec("chmod 644 /etc/provisioner/.env")

#     def load_env_file(self, env_file_path):
#         env_map = EnvFileMappers().envFile().fromFile(str(env_file_path))
#         return {
#             "NAMESPACE": env_map.get("NAMESPACE", "Missing"),
#             "SERVICE_NAME": env_map.get("SERVICE_NAME", "Missing"),
#             "PORT": env_map.get("PORT", "Missing"),
#             "VERSION": env_map.get("VERSION", "Missing"),
#             "DOCKER_NETWORK": env_map.get("DOCKER_NETWORK", "Missing")
#         }

#     def log_env_file(self, env_file):
#         for key, value in env_file.items():
#             logger.info(f"{key}: {value}")

#     def set_env_vars(self, env_file):
#         pass

#     def set_volume_mounts(self):
#         self.with_volume_mapping(os.path.expanduser("~/.ssh"), os.path.expanduser("/root/.ssh"))

#     def set_ports_mapping(self, env_file):
#         # port = int(env_file['PORT'])
#         # self.with_exposed_ports(port)
#         # self.with_bind_ports(port, port)
#         # self.with_exposed_ports(22)
#         # Bind port 22 -> 2222
#         # self.with_bind_ports(22, 2222)

#         self.with_exposed_ports(2222)
#         self.with_bind_ports(22, 2222)


#     def disable_ryuk(self):
#         logger.info("Disabling Ryuk for automatic cleanup")
#         os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"
#         os.environ["testcontainers.ryuk.disabled"] = "true"

#     def exec(self, command):
#         """Execute a command in the container"""
#         if not self._container:
#             logger.error("Attempted to execute a command before starting the container!")
#             return None

#         container = self.get_wrapped_container()  # Get actual container instance
#         if container:
#             try:
#                 result = container.exec_run(command)  # Execute command inside container
#                 if result.exit_code != 0:
#                     logger.warning(f"Command '{command}' failed with exit code {result.exit_code}")
#                     logger.warning(f"Output: {result.output.decode('utf-8')}")
#                 return result
#             except Exception as e:
#                 logger.error(f"Failed to execute command: {command}. Error: {e}")
#         return None

#     def build_image(self):
#         """Build the Docker image locally"""
#         logger.info(f"Building Docker image from: {DEFAULT_REMOTE_SSH_DOCKERFILE_PATH}")
#         try:
#             client = docker.from_env()

#             # Check if image already exists
#             try:
#                 client.images.get(DEFAULT_REMOTE_SSH_IMAGE_NAME)
#                 logger.info(f"Image {DEFAULT_REMOTE_SSH_IMAGE_NAME} already exists")
#                 return
#             except docker.errors.ImageNotFound:
#                 pass

#             # Build the image
#             build_logs = client.api.build(
#                 path=PROJECT_ROOT_PATH,
#                 dockerfile=DEFAULT_REMOTE_SSH_DOCKERFILE_PATH,
#                 tag=DEFAULT_REMOTE_SSH_IMAGE_NAME,
#                 rm=True
#             )

#             # Stream build logs
#             for log in build_logs:
#                 try:
#                     log_line = json.loads(log.decode('utf-8'))
#                     if 'stream' in log_line:
#                         logger.info(log_line['stream'].strip())
#                 except json.JSONDecodeError:
#                     logger.info(log.decode('utf-8').strip())

#         except Exception as e:
#             logger.error(f"Failed to build Docker image: {str(e)}")
#             raise RuntimeError(f"Failed to build Docker image: {str(e)}")

# # Usage Example:
# #
# # def setUp(self):
# #         self.container = RemoteSSHContainer(CoreCollaborators(Context.create_empty()))
# #         self.container.start()

# # def tearDown(self):
# #     if self.container:
# #         self.container.stop()

# # Usage Example:
# # kafka_container = KafkaContainer(core_cols).start()
# # try:
# #     # Run tests
# # finally:
# #     kafka_container.stop()


# #
# # TODO: Move from here to a dedicated collaborator
# #
# class EnvFileMapper:
#     @staticmethod
#     def fromFile(file_path: str) -> Dict[str, str]:
#         """
#         Reads an .env file and returns its contents as a dictionary.

#         Args:
#             file_path (str): Path to the .env file

#         Returns:
#             Dict[str, str]: Dictionary containing environment variables

#         Raises:
#             FileNotFoundError: If the .env file doesn't exist
#             IOError: If there's an error reading the file
#         """
#         env_map = {}

#         # Check if file exists
#         if not os.path.exists(file_path):
#             raise FileNotFoundError(f"Environment file not found: {file_path}")

#         try:
#             with open(file_path, 'r') as file:
#                 for line in file:
#                     # Skip empty lines and comments
#                     line = line.strip()
#                     if not line or line.startswith('#'):
#                         continue

#                     # Handle both = and export KEY=value formats
#                     if line.startswith('export '):
#                         line = line.replace('export ', '', 1)

#                     # Split on first = only
#                     if '=' in line:
#                         key, value = line.split('=', 1)
#                         key = key.strip()
#                         value = value.strip()

#                         # Remove quotes if present
#                         if value.startswith('"') and value.endswith('"'):
#                             value = value[1:-1]
#                         elif value.startswith("'") and value.endswith("'"):
#                             value = value[1:-1]

#                         env_map[key] = value

#         except Exception as e:
#             raise IOError(f"Error reading environment file: {str(e)}")

#         return env_map

# # Example usage:
# class EnvFileMappers:
#     def envFile(self) -> EnvFileMapper:
#         return EnvFileMapper()

# # class Mappers:
# #     def envFile(self) -> EnvFileMapper:
# #         return EnvFileMapper()


# def ensure_network_exists(self, network_name):
#     client = docker.from_env()
#     try:
#         client.networks.get(network_name)
#         print(f"Network {network_name} already exists.")
#     except docker.errors.NotFound:
#         print(f"Creating network: {network_name}")
#         client.networks.create(network_name, driver="bridge")

# def set_network(self, env_file):
#     """
#     Set network configuration for the container using available methods in testcontainers 4.9.1
#     """
#     container_name = f"{env_file['NAMESPACE']}-{env_file['SERVICE_NAME']}"

#     self.with_network(Network(docker_network_kw={
#         'network': 'bridge',
#         'network_mode': 'bridge',
#         'name': container_name,
#         'hostname': container_name
#     }))

#     self.ensure_network_exists(container_name)
#     self.with_network_aliases(container_name)

#     # Alternative approach using environment variables for network configuration
#     self.with_env('CONTAINER_NAME', container_name)
#     self.with_env('HOSTNAME', container_name)

# def set_network(self, env_file):
#     container_name = f"{env_file['NAMESPACE']}-{env_file['SERVICE_NAME']}"
#     self.with_network_mode("bridge")
#     self.with_network_alias(container_name)
