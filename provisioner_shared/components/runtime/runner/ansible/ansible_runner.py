# !/usr/bin/env python3

import os
import re
import tempfile
import threading
import time
from typing import Callable, List, Optional

import ansible_runner
import paramiko
from loguru import logger

from provisioner_shared.components.runtime.errors.cli_errors import (
    AnsiblePassAuthRequireSSHPassException,
    AnsiblePlaybookRunnerException,
    AnsibleRunnerNoHostSSHAccessException,
    InvalidAnsibleHostPair,
)
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.utils.io_utils import IOUtils
from provisioner_shared.components.runtime.utils.os import OsArch
from provisioner_shared.components.runtime.utils.paths import Paths
from provisioner_shared.components.runtime.utils.printer import LeadingIcon, Printer
from provisioner_shared.components.runtime.utils.process import Process
from provisioner_shared.components.runtime.utils.progress_indicator import ProgressIndicator

ProvisionerAnsibleProjectPath = os.path.expanduser("~/.config/provisioner/ansible")

ANSIBLE_HOSTS_FILE_NAME = "hosts"
ANSIBLE_LOCAL_CONNECTION = "ansible_connection=local"

ANSIBLE_CFG_PYTHON_PACKAGE = "provisioner_shared.components.runtime.runner.ansible.resources"
ANSIBLE_CFG_FILE_NAME = "ansible.cfg"
# ANSIBLE_DEFAULT_PYTHON_INTERPRETER_PATH = "/usr/bin/python3"

ANSIBLE_CALLBACK_PLUGINS_PYTHON_PACKAGE = (
    "provisioner_shared.components.runtime.runner.ansible.resources.callback_plugins"
)
ANSIBLE_CALLBACK_PLUGINS_DIR_NAME = "callback_plugins"

ANSIBLE_PLAYBOOKS_PYTHON_PACKAGE = "provisioner_shared.components.external.ansible_playbooks.playbooks"
ANSIBLE_PLAYBOOKS_DIR_NAME = "playbooks"

ANSIBLE_STDOUT_PLUGIN_NAME = "custom_yaml"

ANSIBLE_VALUES_SENSITIVE_KEYWORDS = ["token", "secret", "api_token", "api_secret", "password", "pass", "pwd"]

INVENTORY_FORMAT = """
[all:vars]
ansible_connection=ssh

# These are the user selected hosts from the prompted selection menu
[selected_hosts]
{}
"""

ENV_VARS = {
    "ANSIBLE_CONFIG": f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_CFG_FILE_NAME}",
    "ANSIBLE_CALLBACK_PLUGINS": f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_CALLBACK_PLUGINS_DIR_NAME}",
    "ANSIBLE_STDOUT_CALLBACK": ANSIBLE_STDOUT_PLUGIN_NAME,
    "ANSIBLE_PYTHON_INTERPRETER": "auto",
    "ANSIBLE_DEPRECATION_WARNINGS": "False",
    "ANSIBLE_SYSTEM_WARNINGS": "False",
    "ANSIBLE_COMMAND_WARNINGS": "False",
    "ANSIBLE_ACTION_WARNINGS": "False",
    "ANSIBLE_FORCE_COLOR": "false",
}

REMOTE_MACHINE_LOCAL_BIN_FOLDER = "~/.local/bin"


class AnsiblePlaybook:
    __name: str
    __content: str
    __remote_context: RemoteContext

    def __init__(self, name: str, content: str, remote_context: Optional[RemoteContext] = None) -> None:
        self.__name = name
        self.__content = content
        self.__remote_context = remote_context

    @staticmethod
    def copy_and_add_context(copy_from: "AnsiblePlaybook", remote_context: RemoteContext) -> "AnsiblePlaybook":
        return AnsiblePlaybook(copy_from.__name, copy_from.__content, remote_context)

    def get_name(self) -> str:
        return self.__name.replace(" ", "_").lower()

    def is_remote_run_as_dry_run(self) -> bool:
        return self.__remote_context.is_dry_run() is True

    def get_content(self, paths: Paths, ansible_playbook_package: str, dry_run: bool) -> str:
        """
        Playbook content support the following string format values:
        - {ansible_playbooks_path}: replace with the ansible-playbook resource root folder path
        - {modifiers}: Add modifier flags: DRY_RUN / VERBOSE / SILENT
        """
        resolved_path: str = ""
        if "ansible_playbooks_path" in self.__content:
            resolved_path = self._get_ansible_playbook_path(paths, ansible_playbook_package)

        # TODO: Separate between the {modifiers} section to the XTERM, add two section that
        #       will be added to the playbook content under 'environment:' attribute
        modifiers: str = ""
        # if "modifiers" in self.__content and not dry_run:
        if "modifiers" in self.__content:
            if self.__remote_context is None:
                logger.debug(
                    "Empty remote context, modifiers won't get added to the Ansible playbook (dry_run / verbose / silent)"
                )
            else:
                modifiers = self._generate_modifiers(self.__remote_context)

        return self.__content.format(ansible_playbooks_path=resolved_path, modifiers=modifiers)

    def _generate_modifiers(self, remote_context: RemoteContext):
        # Added TERM=xterm: xterm to allow a unified Linux terminal experience, not all terminals are supported
        if not remote_context.is_dry_run() and not remote_context.is_silent() and not remote_context.is_verbose():
            return """
  environment:
    TERM: xterm
"""
        return f"""
  environment:
    TERM: xterm
    {"DRY_RUN: True" if remote_context.is_dry_run() else ""}
    {"VERBOSE: True" if remote_context.is_verbose() else ""}
    {"SILENT: True" if remote_context.is_silent() else ""}
"""

    def _get_ansible_playbook_path(self, paths: Paths, ansible_playbook_package: str):
        package_dir_split = ansible_playbook_package.rsplit(".", 1)
        package_prefix = package_dir_split[0]
        package_suffix = package_dir_split[0]

        if len(package_dir_split) > 1:
            package_suffix = package_dir_split[1]

        return paths.get_dir_path_from_python_package(package_prefix, package_suffix)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return False

    def __hash__(self):
        return hash((self.__name, self.__content))


class AnsibleHost:

    def __init__(
        self,
        host: str,
        ip_address: str,
        port: Optional[int] = 22,
        username: str = None,
        password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
    ) -> None:

        self.host = host
        self.ip_address = ip_address
        self.port = port
        self.username = username
        self.password = password
        self.ssh_private_key_file_path = ssh_private_key_file_path

    @staticmethod
    def from_dict(ansible_host_dict: dict) -> "AnsibleHost":
        return AnsibleHost(
            host=ansible_host_dict["hostname"],
            ip_address=ansible_host_dict["ip_address"],
            port=ansible_host_dict["port"] if "port" in ansible_host_dict else 22,
            username=ansible_host_dict["username"] if "username" in ansible_host_dict else None,
            password=ansible_host_dict["password"] if "password" in ansible_host_dict else None,
            ssh_private_key_file_path=(
                ansible_host_dict["ssh_private_key_file_path"]
                if "ssh_private_key_file_path" in ansible_host_dict
                else None
            ),
        )


class AnsibleStdFileDescriptors:
    stdout_fd: int
    stderr_fd: int
    stdout_path: str
    stderr_path: str
    ansible_done: threading.Event
    reader_thread: threading.Thread

    def __init__(
        self,
        stdout_fd: int,
        stderr_fd: int,
        stdout_path: str,
        stderr_path: str,
        ansible_done: threading.Event,
        reader_thread: threading.Thread,
    ):
        self.stdout_fd = stdout_fd
        self.stderr_fd = stderr_fd
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.ansible_done = ansible_done
        self.reader_thread = reader_thread


class AnsibleRunnerLocal:

    _os_arch: OsArch = None
    _dry_run: bool = None
    _verbose: bool = None
    _paths: Paths = None
    _io_utils: IOUtils = None
    _process: Process = None
    _progress: ProgressIndicator = None
    _printer: Printer = None

    def __init__(
        self,
        io_utils: IOUtils,
        paths: Paths,
        process: Process,
        progress: ProgressIndicator,
        printer: Printer,
        ctx: Context,
    ) -> None:

        self._io_utils = io_utils
        self._paths = paths
        self._process = process
        self._progress = progress
        self._printer = printer
        self._dry_run = ctx.is_dry_run()
        self._verbose = ctx.is_verbose()
        self._os_arch = ctx.os_arch

    @staticmethod
    def create(
        ctx: Context, io_utils: IOUtils, paths: Paths, process: Process, progress: ProgressIndicator, printer: Printer
    ) -> "AnsibleRunnerLocal":

        logger.debug(f"Creating Ansible runner (dry_run: {ctx.is_dry_run()}, verbose: {ctx.is_verbose()})...")
        return AnsibleRunnerLocal(io_utils, paths, process, progress, printer, ctx)

    def _prepare_ansible_host_items(self, ansible_hosts: List[AnsibleHost]) -> List[str]:
        result = []

        if self._dry_run and len(ansible_hosts) == 0:
            return result

        for host in ansible_hosts:
            if not host.host or not host.ip_address and not self._dry_run:
                err_msg = f"Ansible selected host is missing manadatory arguments. host: {host.host}, ip: {host.ip_address}, port: {host.port}"
                logger.error(err_msg)
                raise InvalidAnsibleHostPair(err_msg)

            # Do not append 'ansible_host=' prefix for local connection
            if ANSIBLE_LOCAL_CONNECTION in host.ip_address:
                result.append(f"{host.host} {host.ip_address}")
            else:
                host_entry = f"{host.host} ansible_host={host.ip_address} ansible_user={host.username} ansible_port={host.port} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'"
                if host.password:
                    # k8s-master ansible_host=1.1.1.1 ansible_user=user1 ansible_password=password1
                    host_entry += f" ansible_password={host.password}"
                if host.ssh_private_key_file_path:
                    # k8s-node1 ansible_host=1.1.1.2 ansible_user=user2 ansible_private_key_file=~/.ssh/rsa_key
                    host_entry += f" ansible_private_key_file={host.ssh_private_key_file_path}"
                result.append(host_entry)

        return result

    def _create_ansible_config_file(self):
        # Copy config file to ~/.config/provisioner/ansible/ansible.cfg
        ansible_cfg_src_filepath = self._paths.get_file_path_from_python_package(
            ANSIBLE_CFG_PYTHON_PACKAGE, ANSIBLE_CFG_FILE_NAME
        )
        ansible_cfg_dest_filepath = f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_CFG_FILE_NAME}"
        self._io_utils.create_directory_fn(ProvisionerAnsibleProjectPath)
        self._io_utils.copy_file_fn(from_path=ansible_cfg_src_filepath, to_path=ansible_cfg_dest_filepath)
        logger.debug(f"Copied ansible.cfg file. source: {ansible_cfg_src_filepath}, dest: {ansible_cfg_dest_filepath}")

    def _create_ansible_callback_plugins_folder(self) -> str:
        # Copy callback plugins file to ~/.config/provisioner/ansible/callback_plugins
        callbacks_src_dir = self._paths.get_dir_path_from_python_package(
            ANSIBLE_CFG_PYTHON_PACKAGE, ANSIBLE_CALLBACK_PLUGINS_DIR_NAME
        )
        callbacks_dest_dir = self._io_utils.create_directory_fn(
            f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_CALLBACK_PLUGINS_DIR_NAME}"
        )
        self._io_utils.copy_directory_fn(from_path=callbacks_src_dir, to_path=callbacks_dest_dir)
        logger.debug(f"Copied ansible callback plugins. source: {callbacks_src_dir}, dest: {callbacks_dest_dir}")

    def _create_inventory_hosts_file(self, selected_hosts: List[AnsibleHost]) -> str:
        ansible_hosts_list = self._prepare_ansible_host_items(selected_hosts)
        hosts_list = "\n".join(ansible_hosts_list)
        inventory = INVENTORY_FORMAT.format(hosts_list)
        hosts_file_path = self._io_utils.write_file_fn(
            content=inventory, file_name=ANSIBLE_HOSTS_FILE_NAME, dir_path=ProvisionerAnsibleProjectPath
        )
        logger.debug(f"Created ansible hosts file. path: {hosts_file_path}")

    def _generate_ansible_playbook_args(
        self,
        playbook_file_path: str,
        ansible_vars: Optional[List[str]] = None,
        ansible_tags: Optional[List[str]] = None,
        is_dry_run: Optional[bool] = False,
    ) -> List[str]:

        cmdline_args = [
            "-i",
            f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_HOSTS_FILE_NAME}",
            playbook_file_path,
            # "-e",
            # f"ansible_python_interpreter=auto",
            "-e",
            f"local_bin_folder='{REMOTE_MACHINE_LOCAL_BIN_FOLDER}'",
            "-e",
            f"dry_run={is_dry_run}",
        ]
        if ansible_vars:
            cmdline_args += [f"-e {ansible_var}" for ansible_var in ansible_vars]

        tags_str = ""
        if ansible_tags:
            tags_sep = ""
            for ansible_tag in ansible_tags:
                tags_str += f"{tags_sep}{ansible_tag}"
                tags_sep = ","

        if self._os_arch:
            sep = "," if len(tags_str) > 0 else ""
            tags_str += f"{sep}{self._os_arch.os}"

        cmdline_args += ["--tags"] + [tags_str]

        if self._verbose:
            # cmdline_args += ["-vvvv"]
            cmdline_args += ["-v"]
        # for host in selected_hosts:
        #     if host.password:
        #         cmdline_args += ['-b', '-c', 'paramiko', '--ask-pass']
        return cmdline_args

    def _create_playbook_file(self, name: str, content: str) -> str:
        playbooks_dest_dir = self._io_utils.create_directory_fn(
            f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_PLAYBOOKS_DIR_NAME}"
        )
        logger.debug(f"Created playbook file. path: {playbooks_dest_dir}\n{content}")
        return self._io_utils.write_file_fn(content=content, file_name=name, dir_path=playbooks_dest_dir)

    def _clear_sensitive_data_from_args(self, ansible_args: Optional[List[str]] = None) -> str:
        if not ansible_args or len(ansible_args) == 0:
            return ansible_args
        reduced_args: List[str] = []
        for ansible_var in ansible_args:
            key_value = ansible_var.split("=")
            if len(key_value) == 2:
                ansible_var_key = key_value[0]
                found = False
                for keyword in ANSIBLE_VALUES_SENSITIVE_KEYWORDS:
                    if keyword in ansible_var_key:
                        found = True
                        reduced_args.append(f"{ansible_var_key}=REDACTED")
                if not found:
                    reduced_args.append(ansible_var)
            else:
                reduced_args.append(ansible_var)
        return reduced_args

    def _run(
        self,
        selected_hosts: List[AnsibleHost],
        playbook: AnsiblePlaybook,
        ansible_vars: Optional[List[str]] = None,
        ansible_tags: Optional[List[str]] = None,
        ansible_playbook_package: Optional[str] = ANSIBLE_PLAYBOOKS_PYTHON_PACKAGE,
    ) -> str:

        # Problem:
        # To use ansible-playground with host entry that uses ansible_password=secret
        # we must have sshpass installed locally
        # ERROR:
        # to use the 'ssh' connection type with passwords or pkcs11_provider,
        # you must install the sshpass program
        #
        if self.is_password_was_used_in_hosts(selected_hosts) and not self._process._is_tool_exist("sshpass"):
            raise AnsiblePassAuthRequireSSHPassException(
                "SSH password authentication requires utility to be installed. name: sshpass"
            )

        # Solution:
        # It is possible to pass the parameter using paramiko,
        # which is another pure python implementation of SSH.
        # This is supported by ansible and would be the preferred option
        # as it relies on less cross language dependancies that has to be separately managed;
        # Thus this essentially by-passes the need for another library installed
        # on the host machine : sshpass.
        self._create_ansible_config_file()
        self._create_ansible_callback_plugins_folder()
        self._create_inventory_hosts_file(selected_hosts)
        self._check_ssh_conn_on_hosts(ansible_hosts=selected_hosts)

        playbook_content_escaped = playbook.get_content(self._paths, ansible_playbook_package, self._dry_run)
        playbook_file_path = self._create_playbook_file(name=playbook.get_name(), content=playbook_content_escaped)
        ansible_playbook_args: List[str] = self._generate_ansible_playbook_args(
            playbook_file_path, ansible_vars, ansible_tags, playbook.is_remote_run_as_dry_run()
        )
        ansible_playbook_args_reducted = self._clear_sensitive_data_from_args(ansible_playbook_args)
        logger.debug(f"About to run command:\nansible-playbook {' '.join(map(str, ansible_playbook_args_reducted))}")
        # logger.debug(f"About to run command:\nansible-playbook {' '.join(map(str, ansible_playbook_args))}")

        if self._dry_run:
            return f"name: {playbook.get_name()}\ncontent:\n{playbook_content_escaped}\ncommand:\nansible-playbook {' '.join(map(str, ansible_playbook_args_reducted))}"

        file_descriptors = self.prepare_file_descriptors(self._verbose)
        out, err, rc = self._run_and_capture_ansible_output(
            file_descriptors,
            lambda: ansible_runner.run_command(
                private_data_dir=ProvisionerAnsibleProjectPath,
                executable_cmd="ansible-playbook",
                cmdline_args=ansible_playbook_args,
                runner_mode="subprocess",
                envvars=ENV_VARS,
                quiet=False,
                # input_fd=sys.stdin,
                output_fd=file_descriptors.stdout_fd,
                error_fd=file_descriptors.stderr_fd,
            ),
        )

        # Handle non-zero return codes
        if rc != 0:
            self.handle_failure_exit_code(out, err)

        if self._verbose:
            return str(out)
        else:
            return self.extract_ansible_msg_content(out)

    def handle_failure_exit_code(self, out: str, err: str) -> None:
        message = err if err else out

        # Check if this is a Python interpreter discovery warning or other benign warning
        python_interpreter_warning = any(
            [
                "[WARNING]: Platform linux on host" in message and "using the discovered Python interpreter" in message,
                "[WARNING]: Python interpreter discovery" in message,
                "but future installation of another Python interpreter could change" in message,
            ]
        )

        if python_interpreter_warning:
            logger.warning("Python interpreter discovery warning detected, but continuing execution")
        else:
            # If verbose is not enabled, try to extract a more relevant error message
            if not err and not self._verbose:
                message = self._try_extract_stderr_message(message)
            raise AnsiblePlaybookRunnerException(message)

    def _run_and_capture_ansible_output(
        self, file_descriptors: AnsibleStdFileDescriptors, ansible_runner_call: Callable[..., tuple[str, str, int]]
    ) -> tuple[str, str, int]:
        out = ""
        err = ""
        rc = 0

        try:
            # Return tuple (out, err, rc), we ignore out and err
            # and use the file descriptors to read the output
            _, _, rc = ansible_runner_call()

            # Signal that ansible has completed
            file_descriptors.ansible_done.set()

            # Wait for reader thread to finish
            file_descriptors.reader_thread.join(timeout=2)

            # Read the full output for return values
            with open(file_descriptors.stdout_path, "r") as f:
                out = f.read()
            with open(file_descriptors.stderr_path, "r") as f:
                err = f.read()

        except Exception as e:
            logger.error(f"Error running ansible-playbook: {e}")

        finally:
            # Close file descriptors
            file_descriptors.stdout_fd.close()
            file_descriptors.stderr_fd.close()

            # Clean up temp files
            try:
                os.unlink(file_descriptors.stdout_path)
                os.unlink(file_descriptors.stderr_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp files: {e}")

        return out, err, rc

    def prepare_file_descriptors(self, is_verbose: bool) -> AnsibleStdFileDescriptors:
        # Create temp files for stdout and stderr
        stdout_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        stderr_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)

        stdout_path = stdout_file.name
        stderr_path = stderr_file.name

        # Close the file objects so ansible_runner can open them for writing
        stdout_file.close()
        stderr_file.close()

        # Create file objects for ansible_runner
        stdout_fd = open(stdout_path, "w")
        stderr_fd = open(stderr_path, "w")

        # Thread function to read and filter task names
        def read_and_filter(file_path):
            with open(file_path, "r") as f:
                # Go to end of file
                f.seek(0, os.SEEK_END)

                while True:
                    line = f.readline()
                    if not line:
                        # If ansible_runner process has completed, exit
                        if ansible_done.is_set():
                            break
                        # Otherwise wait for more content
                        time.sleep(0.1)
                        continue

                    # Extract task names
                    task_match = re.search(r"TASK \[.*?: (.*?)\]", line)
                    if task_match:
                        task_name = task_match.group(1)
                        if task_name != "debug":
                            print(f"Running task: {task_name}")

        # Flag to signal when ansible has completed
        ansible_done = threading.Event()

        # Start reader thread
        reader_thread = threading.Thread(target=read_and_filter, args=(stdout_path,))
        reader_thread.daemon = True
        reader_thread.start()

        return AnsibleStdFileDescriptors(stdout_fd, stderr_fd, stdout_path, stderr_path, ansible_done, reader_thread)

    def is_password_was_used_in_hosts(self, selected_hosts: List[AnsibleHost]) -> bool:
        for selected_host in selected_hosts:
            if selected_host.password is not None:
                return True
        return False

    def _try_extract_stderr_message(self, ansible_run_output: str) -> str:
        match = re.search(r"stderr: \|-\s+(.*?)\s+stderr_lines:", ansible_run_output, re.DOTALL)
        extracted_text = ansible_run_output
        if match:
            extracted_text = match.group(1)
        else:
            logger.debug("Could not find Ansible stderr in playbook output")
        return extracted_text

    def extract_ansible_msg_content(self, ansible_output: str) -> str:
        """
        Extract content between 'msg:' and the next Ansible section (TASK, PLAY, etc.)

        Args:
            ansible_output: Raw Ansible output text

        Returns:
            Extracted message contents with all leading spaces removed
        """
        if not ansible_output:
            return ""

        # Pattern to match 'msg:' content blocks
        pattern = r"(?:^|\n)\s*msg: (?:\|-|\|2-)?\s*\n(.*?)(?=\n\s*(?:TASK|PLAY|RUNNING|ok:|changed:|fatal:|skipped:|failed:)|\Z)"

        # Find all matches in the text
        matches = re.finditer(pattern, ansible_output, re.DOTALL | re.MULTILINE)

        # Extract and clean up each match
        extracted_messages = []
        for match in matches:
            # Process each line to forcibly remove ALL leading spaces
            lines = match.group(1).splitlines()
            cleaned_lines = []

            for line in lines:
                # Strip all leading spaces for every line
                cleaned_lines.append(line.lstrip())

            # Join back and add to results
            extracted_messages.append("\n".join(cleaned_lines).strip())

        return "\n".join(extracted_messages)

    def _check_ssh_conn_on_hosts(self, ansible_hosts: List[AnsibleHost]) -> None:
        if self._dry_run:
            return
        
        for selected_host in ansible_hosts:
            if selected_host.ip_address == ANSIBLE_LOCAL_CONNECTION:
                continue
            self._wait_for_ssh(selected_host)

    def _wait_for_ssh(self, host: AnsibleHost) -> None:
        """Ensure SSH is ready before proceeding."""
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if host.password:
                    client.connect(host.ip_address, port=host.port, username=host.username, password=host.password)
                else:
                    client.connect(
                        host.ip_address,
                        port=host.port,
                        username=host.username,
                        key_filename=host.ssh_private_key_file_path,
                    )
                # print("✅ SSH Connection Successful")
                self._printer.print_fn("SSH Connection Successful", LeadingIcon.CHECKMARK)
                client.close()
                return
            except Exception:
                self._printer.print_fn(f"🔄 Waiting for SSH... ({attempt + 1}/{max_attempts})")
                time.sleep(2)
                attempt += 1
        raise AnsibleRunnerNoHostSSHAccessException(
            f"❌ No SSH access to host. name: {host.host}, ip: {host.ip_address}, port: {host.port}"
        )

    run_fn = _run
