#!/usr/bin/env python3

from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.hosts_file import HostsFile
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil


class FakeHostsFile(HostsFile):
    class EntryArgs:
        ip_address: str = None
        dns_names: List[str] = None
        comment: str = None
        entry_type: str = None

        def __init__(self, ip_address: str, dns_names: List[str], comment: str, entry_type: str) -> None:
            self.ip_address = ip_address.strip() if ip_address else None
            self.dns_names = dns_names
            self.comment = comment.strip() if comment else None
            self.entry_type = entry_type.strip() if entry_type else None

        def __eq__(self, other: object) -> bool:
            if isinstance(other, FakeHostsFile.EntryArgs):
                return hash(self) == hash(other)
            return False

        def __hash__(self):
            return hash((self.ip_address, str(self.dns_names), self.comment, self.entry_type))

    json_util: JsonUtil = None
    registered_added_entries_hashes: List[EntryArgs] = None

    args1: EntryArgs = None
    args2: EntryArgs = None

    def __init__(self, dry_run: bool, verbose: bool, json_util: JsonUtil):
        super().__init__(process=None, dry_run=dry_run, verbose=verbose)
        self.registered_added_entries_hashes = []
        self.json_util = json_util

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool, json_util: JsonUtil) -> "FakeHostsFile":
        hosts_file = FakeHostsFile(dry_run=dry_run, verbose=verbose, json_util=json_util)
        hosts_file.add_entry_fn = (
            lambda ip_address, dns_names, comment=None, entry_type="ipv4": hosts_file._register_added_entry(
                ip_address, dns_names, comment, entry_type
            )
        )
        return hosts_file

    @staticmethod
    def create(ctx: Context) -> "FakeHostsFile":
        json_util = JsonUtil.create(ctx, IOUtils.create(ctx))
        return FakeHostsFile._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose(), json_util=json_util)

    def _register_added_entry(self, ip_address: str, dns_names: List[str], comment: str, entry_type: str) -> None:
        args = FakeHostsFile.EntryArgs(ip_address, dns_names, comment, entry_type)
        self.registered_added_entries_hashes.append(args)

    def assert_entry_added(
        self, ip_address: str, dns_names: List[str], comment: str = None, entry_type: str = "ipv4"
    ) -> None:
        args = FakeHostsFile.EntryArgs(ip_address, dns_names, comment, entry_type)
        if args not in self.registered_added_entries_hashes:
            args_json = self.json_util.to_json_fn(args)
            raise FakeEnvironmentAssertionError(f"Hosts file entry expected but never added. args:\n{args_json}")
