#!/usr/bin/env python3

from typing import Optional
from unittest.mock import MagicMock

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.network import NetworkUtil
from provisioner_shared.test_lib.faker import TestFakes


class FakeNetworkUtil(TestFakes, NetworkUtil):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        NetworkUtil.__init__(self, None, None, dry_run=dry_run, verbose=verbose)

    @staticmethod
    def create(ctx: Context) -> "FakeNetworkUtil":
        fake = FakeNetworkUtil(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.get_all_lan_network_devices_fn = MagicMock(side_effect=fake.get_all_lan_network_devices_fn)
        return fake

    def get_all_lan_network_devices_fn(self, ip_range: str, dns_server: Optional[str] = None, filter_str: Optional[str] = None) -> bool:
        return self.trigger_side_effect("get_all_lan_network_devices_fn", ip_range, dns_server, filter_str)
