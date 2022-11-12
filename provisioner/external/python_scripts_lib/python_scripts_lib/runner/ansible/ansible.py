#!/usr/bin/env python3

import json
from typing import List, Optional

from loguru import logger

from ...errors.cli_errors import ExternalDependencyFileNotFound, InvalidAnsibleHostPair
from ...infra.context import Context
from ...utils.io_utils import IOUtils
from ...utils.process import Process

ANSIBLE_SHELL_RUNNER_PATH = "external/shell_scripts_lib/runner/ansible/ansible.sh"


class HostIpPair:
    host: str
    ip_address: str

    def __init__(self, host: str, ip_address: str) -> None:
        self.host = host
        self.ip_address = ip_address

class AnsibleRunner:

    _dry_run: bool = None
    _verbose: bool = None
    _process: Process = None
    _io_utils: IOUtils = None
    _ansible_shell_runner_path: str = None

    def __init__(
        self, io_utils: IOUtils, process: Process, dry_run: bool, verbose: bool, ansible_shell_runner_path: str
    ) -> None:

        self._io_utils = io_utils
        self._process = process
        self._dry_run = dry_run
        self._verbose = verbose
        self._ansible_shell_runner_path = ansible_shell_runner_path

    @staticmethod
    def create(
        ctx: Context,
        io_utils: IOUtils,
        process: Process,
        ansible_shell_runner_path: Optional[str] = ANSIBLE_SHELL_RUNNER_PATH,
    ) -> "AnsibleRunner":

        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating Ansible runner (dry_run: {dry_run}, verbose: {verbose})...")
        return AnsibleRunner(io_utils, process, dry_run, verbose, ansible_shell_runner_path)

    def _generate_call_parameter_list(self, param_name: str, params: List[str]) -> List[str]:
        result_list = []
        if params and len(params) > 0:
            for param in params:
                result_list.append(f"{param_name}: {param}")
        return result_list

    def _verify_ansible_runner_script(self):
        if not self._io_utils.file_exists_fn(file_path=self._ansible_shell_runner_path):
            err_msg = f"Ansible runner external script not found. path: {self._ansible_shell_runner_path}"
            logger.error(err_msg)
            raise ExternalDependencyFileNotFound(err_msg)
        logger.debug("Ansible runner external script was found")

    def _prepare_ansible_host_items(self, host_ip_pair_list: List[HostIpPair]) -> List[str]:
        result = []

        if self._dry_run:
            return result

        for pair in host_ip_pair_list:
            if not pair.host or not pair.ip_address and not self._dry_run:
                err_msg = f"Ansible selected hosts are not in expected pair (host, ip). host: {pair.host}, ip: {pair.ip_address}"
                logger.error(err_msg)
                raise InvalidAnsibleHostPair(err_msg)

            # Do not append 'ansible_host=' prefix for local connection
            if "ansible_connection=local" in pair.ip_address:
                result.append(f"{pair.host} {pair.ip_address}")
            else:
                result.append(f"{pair.host} ansible_host={pair.ip_address}")

        return result

    def _run(
        self,
        username: str,
        working_dir: str,
        selected_hosts: List[HostIpPair],
        playbook_path: str,
        password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ansible_vars: Optional[List[str]] = None,
        ansible_tags: Optional[List[str]] = None,
        force_dockerized: Optional[bool] = False,
    ) -> str:

        """
        Call the ansible shell runner to trigger an ansible playbook.
        Selected hosts are pairs of (hostname ip_address)
        For additional information please refer to the file located at
        ANSIBLE_SHELL_RUNNER_PATH
        """
        if not self._dry_run:
            self._verify_ansible_runner_script()

        ansible_hosts_list = self._prepare_ansible_host_items(selected_hosts)
        selected_hosts_items_list = self._generate_call_parameter_list("selected_host", ansible_hosts_list)
        ansible_vars_items_list = self._generate_call_parameter_list("ansible_var", ansible_vars)
        ansible_tags_items_list = self._generate_call_parameter_list("ansible_tag", ansible_tags)

        auth_param = ""
        if password:
            auth_param = f"password: {password}"
        elif ssh_private_key_file_path:
            auth_param = f"ssh_private_key_file_path: {ssh_private_key_file_path}"

        run_cmd = [
            "bash",
            f"./{self._ansible_shell_runner_path}",
            f"working_dir: {working_dir}",
            f"username: {username}",
            auth_param,
            f"playbook_path: {playbook_path}",
        ]

        if len(selected_hosts_items_list) > 0:
            run_cmd += selected_hosts_items_list
        if len(ansible_vars_items_list) > 0:
            run_cmd += ansible_vars_items_list
        if len(ansible_tags_items_list) > 0:
            run_cmd += ansible_tags_items_list

        if force_dockerized:
            run_cmd.append("--force-dockerized")
        if self._dry_run:
            run_cmd.append("--dry-run")
        if self._verbose:
            run_cmd.append("--verbose")

        return self._process.run_fn(args=run_cmd)

    run_fn = _run
