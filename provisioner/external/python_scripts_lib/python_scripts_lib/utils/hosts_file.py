#!/usr/bin/env python3

import os
import tempfile
from typing import List, Optional

from loguru import logger
from python_hosts import Hosts, HostsEntry

from ..infra.context import Context
from .process import Process


class HostsFile:

    _dry_run: bool = None
    _verbose: bool = None
    process: Process = None

    def __init__(self, process: Process, dry_run: bool, verbose: bool) -> None:
        self._dry_run = dry_run
        self._verbose = verbose
        self.process = process

    @staticmethod
    def create(ctx: Context, process: Process) -> "HostsFile":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating hosts file manager (dry_run: {dry_run}, verbose: {verbose})...")
        return HostsFile(process, dry_run, verbose)

    def _add_entry(
        self, ip_address: str, dns_names: List[str], comment: Optional[str] = None, entry_type: Optional[str] = "ipv4"
    ) -> None:

        if self._dry_run:
            return

        hosts_mgr = Hosts()
        new_entry = HostsEntry(entry_type=entry_type, address=ip_address, names=dns_names, comment=comment)
        hosts_mgr.remove_all_matching(address=ip_address)
        hosts_mgr.add([new_entry])
        self._write_hosts_file(hosts_mgr=hosts_mgr)

    def _write_hosts_file(self, hosts_mgr: Hosts) -> None:
        """
        Write to temp file and overwrite real /etc/hosts
        Using 'sudo' it'll prompt the user for password
        """
        tmp_dir = self._get_temp_dir()
        tmp_hosts_file_path = f"{tmp_dir}/hosts"
        write_counts = hosts_mgr.write(path=tmp_hosts_file_path)
        logger.debug(f"Hosts file write counts: {write_counts}")
        self.process.run_fn([f"sudo mv {tmp_hosts_file_path} /etc/hosts"], allow_single_shell_command_str=True)

    def _get_temp_dir(self) -> str:
        return tempfile.mkdtemp(prefix="provisioner-hosts")

    add_entry_fn = _add_entry
