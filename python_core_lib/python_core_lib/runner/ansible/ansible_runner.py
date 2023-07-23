# !/usr/bin/env python3

import os
import re
from typing import List, Optional

import ansible_runner
from loguru import logger

from python_core_lib.errors.cli_errors import (
    AnsiblePlaybookRunnerException,
    InvalidAnsibleHostPair,
)
from python_core_lib.infra.context import Context
from python_core_lib.infra.remote_context import RemoteContext
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.os import OsArch
from python_core_lib.utils.paths import Paths

ProvisionerAnsibleProjectPath = os.path.expanduser("~/.config/provisioner/ansible")

ANSIBLE_HOSTS_FILE_NAME = "hosts"

ANSIBLE_CFG_PYTHON_PACKAGE = "python_core_lib.runner.ansible.resources"
ANSIBLE_CFG_FILE_NAME = "ansible.cfg"

ANSIBLE_CALLBACK_PLUGINS_PYTHON_PACKAGE = "python_core_lib.runner.ansible.resources.callback_plugins"
ANSIBLE_CALLBACK_PLUGINS_DIR_NAME = "callback_plugins"

ANSIBLE_PLAYBOOKS_PYTHON_PACKAGE = "external.ansible_playbooks.playbooks"
ANSIBLE_PLAYBOOKS_DIR_NAME = "playbooks"

ANSIBLE_STDOUT_PLUGIN_NAME = "custom_yaml"

ANSIBLE_VALUES_SENSITIVE_KEYWORDS = ["token", "secret"]

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
        if not remote_context.is_dry_run() and not remote_context.is_silent() and not remote_context.is_verbose():
            return ""
        return f"""
  environment:
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
    host: str
    ip_address: str
    username: str
    password: str
    ssh_private_key_file_path: str

    def __init__(
        self,
        host: str,
        ip_address: str,
        username: str = None,
        password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
    ) -> None:

        self.host = host
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.ssh_private_key_file_path = ssh_private_key_file_path

    @staticmethod
    def from_dict(ansible_host_dict: dict) -> "AnsibleHost":
        return AnsibleHost(
            host=ansible_host_dict["hostname"],
            ip_address=ansible_host_dict["ip_address"],
            username=ansible_host_dict["username"] if "username" in ansible_host_dict else None,
            password=ansible_host_dict["password"] if "password" in ansible_host_dict else None,
            ssh_private_key_file_path=ansible_host_dict["ssh_private_key_file_path"]
            if "ssh_private_key_file_path" in ansible_host_dict
            else None,
        )


class AnsibleRunnerLocal:

    _os_arch: OsArch = None
    _dry_run: bool = None
    _verbose: bool = None
    _paths: Paths = None
    _io_utils: IOUtils = None

    def __init__(
        self,
        io_utils: IOUtils,
        paths: Paths,
        ctx: Context,
    ) -> None:

        self._io_utils = io_utils
        self.paths = paths
        self._dry_run = ctx.is_dry_run()
        self._verbose = ctx.is_verbose()
        self._os_arch = ctx.os_arch

    @staticmethod
    def create(
        ctx: Context,
        io_utils: IOUtils,
        paths: Paths,
    ) -> "AnsibleRunnerLocal":

        logger.debug(f"Creating Ansible runner (dry_run: {ctx.is_dry_run()}, verbose: {ctx.is_verbose()})...")
        return AnsibleRunnerLocal(io_utils, paths, ctx)

    def _prepare_ansible_host_items(self, ansible_hosts: List[AnsibleHost]) -> List[str]:
        result = []

        if self._dry_run and len(ansible_hosts) == 0:
            return result

        for host in ansible_hosts:
            if not host.host or not host.ip_address and not self._dry_run:
                err_msg = (
                    f"Ansible selected host is missing a manadatory arguments. host: {host.host}, ip: {host.ip_address}"
                )
                logger.error(err_msg)
                raise InvalidAnsibleHostPair(err_msg)

            # Do not append 'ansible_host=' prefix for local connection
            if "ansible_connection=local" in host.ip_address:
                result.append(f"{host.host} {host.ip_address}")
            else:
                host_entry = f"{host.host} ansible_host={host.ip_address} ansible_user={host.username}"
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
        ansible_cfg_src_filepath = self.paths.get_file_path_from_python_package(
            ANSIBLE_CFG_PYTHON_PACKAGE, ANSIBLE_CFG_FILE_NAME
        )
        ansible_cfg_dest_filepath = f"{ProvisionerAnsibleProjectPath}/{ANSIBLE_CFG_FILE_NAME}"
        self._io_utils.create_directory_fn(ProvisionerAnsibleProjectPath)
        self._io_utils.copy_file_fn(from_path=ansible_cfg_src_filepath, to_path=ansible_cfg_dest_filepath)
        logger.debug(f"Copied ansible.cfg file. source: {ansible_cfg_src_filepath}, dest: {ansible_cfg_dest_filepath}")

    def _create_ansible_callback_plugins_folder(self) -> str:
        # Copy callback plugins file to ~/.config/provisioner/ansible/callback_plugins
        callbacks_src_dir = self.paths.get_dir_path_from_python_package(
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
            cmdline_args += ["-vvvv"]
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

        playbook_content_escaped = playbook.get_content(self.paths, ansible_playbook_package, self._dry_run)
        playbook_file_path = self._create_playbook_file(name=playbook.get_name(), content=playbook_content_escaped)
        ansible_playbook_args = self._generate_ansible_playbook_args(
            playbook_file_path, ansible_vars, ansible_tags, playbook.is_remote_run_as_dry_run()
        )
        ansible_playbook_args_reducted = self._clear_sensitive_data_from_args(ansible_playbook_args)
        logger.debug(f"About to run command:\nansible-playbook {' '.join(map(str, ansible_playbook_args_reducted))}")
        # logger.debug(f"About to run command:\nansible-playbook {' '.join(map(str, ansible_playbook_args))}")

        if self._dry_run:
            return f"name: {playbook.get_name()}\ncontent:\n{playbook_content_escaped}\ncommand:\nansible-playbook {' '.join(map(str, ansible_playbook_args_reducted))}"

        # Run ansible/generic commands in interactive mode locally
        out, err, rc = ansible_runner.run_command(
            private_data_dir=ProvisionerAnsibleProjectPath,
            executable_cmd="ansible-playbook",
            cmdline_args=ansible_playbook_args,
            runner_mode="subprocess",
            # json_mode=True,
            # timeout=10,
            envvars=ENV_VARS,
            quiet=True,
            # input_fd=sys.stdin if self._verbose else None,
            # output_fd=sys.stdout if self._verbose else None,
            # error_fd=sys.stderr if self._verbose else None,
        )

        if rc != 0:
            message = err if err else out
            # If verbose enabled, we'll send the entire playbook log output
            if not err and not self._verbose:
                message = self._try_extract_stderr_message(message)
            raise AnsiblePlaybookRunnerException(message)

        if self._verbose:
            return str(out)
        else:
            return self._try_extract_stdout_message(out)

    def _try_extract_stderr_message(self, ansible_run_output: str) -> str:
        match = re.search(r"stderr: \|-\s+(.*?)\s+stderr_lines:", ansible_run_output, re.DOTALL)
        extracted_text = ansible_run_output
        if match:
            extracted_text = match.group(1)
        else:
            logger.debug("Could not find Ansible stderr in playbook output")
        return extracted_text

    def _try_extract_stdout_message(self, ansible_run_output: str) -> str:
        # match = re.search(r'msg: \|-\s+(.*?)\s+PLAY RECAP', ansible_run_output, re.DOTALL)
        match = re.search(r"(?<=msg: \|2-)(.*?)(?=PLAY RECAP)", ansible_run_output, re.DOTALL)
        extracted_text = ansible_run_output
        if match:
            extracted_text = match.group(1)
        else:
            logger.debug("Could not find Ansible stdout in playbook output")
        return extracted_text

    run_fn = _run
