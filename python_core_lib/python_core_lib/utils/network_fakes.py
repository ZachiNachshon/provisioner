#!/usr/bin/env python3

from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.network import NetworkUtil


class FakeNetworkUtil(NetworkUtil):

    __registered_lan_network_scanned_ip_ranges: List[str] = None

    __mocked_lan_network_devices_response: dict[str, dict] = None

    def __init__(self, dry_run: bool, verbose: bool):
        super().__init__(printer=None, dry_run=dry_run, verbose=verbose)
        self.__registered_lan_network_scanned_ip_ranges = []
        self.__mocked_lan_network_devices_response = {}

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeNetworkUtil":
        network_util = FakeNetworkUtil(dry_run=dry_run, verbose=verbose)
        network_util.get_all_lan_network_devices_fn = lambda ip_range, filter_str=None, show_progress=False: network_util.__register_lan_network_scanned_ip_ranges(
            ip_range
        )
        return network_util

    @staticmethod
    def create(ctx: Context) -> "FakeNetworkUtil":
        return FakeNetworkUtil._create_fake(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def mock_lan_network_devices_response(self, ip_range: str, response: dict):
        """
        Register response dict of structure:
        {"ip_address": 1.1.1.1, "hostname": test-name, "status": Up/Unknown}
        """
        self.__mocked_lan_network_devices_response[ip_range] = response

    def assert_lan_network_scanned_ip_range(self, ip_range: str) -> None:
        if ip_range not in self.__registered_lan_network_scanned_ip_ranges:
            raise FakeEnvironmentAssertionError(
                f"Network util expected a specific IP range which never fulfilled. ip_range: {ip_range}"
            )

    def __register_lan_network_scanned_ip_ranges(self, ip_range: str) -> dict:
        if ip_range in self.__mocked_lan_network_devices_response:
            return self.__mocked_lan_network_devices_response[ip_range]
        return None
