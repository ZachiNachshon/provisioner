#!/usr/bin/env python3

from typing import List, Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.hosts_file import HostsFile


class FakeHostsFile(TestFakes, HostsFile):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        HostsFile.__init__(self, process=None, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakeHostsFile":
        fake = FakeHostsFile(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.add_entry_fn = MagicMock(side_effect=fake.add_entry_fn)
        return fake

    def add_entry_fn(
        self, ip_address: str, dns_names: List[str], comment: Optional[str] = None, entry_type: Optional[str] = "ipv4"
    ) -> None:
        return self.trigger_side_effect("add_entry_fn", ip_address, dns_names, comment, entry_type)
