#!/usr/bin/env python3

from ..infra.context import Context
from .network import NetworkUtil
from .printer import Printer
from .printer_fakes import FakePrinter


class FakeNetworkUtil(NetworkUtil):

    registered_scan_results: dict[str, dict] = None

    def __init__(self, printer: Printer, dry_run: bool, verbose: bool):
        super().__init__(printer=printer, dry_run=dry_run, verbose=verbose)
        self.registered_scan_results = {}

    @staticmethod
    def _create_fake(printer: Printer, dry_run: bool, verbose: bool) -> "FakeNetworkUtil":
        network_util = FakeNetworkUtil(printer=printer, dry_run=dry_run, verbose=verbose)
        network_util.get_all_lan_network_devices_fn = (
            lambda ip_range, filter_str=None, show_progress=False: network_util._scan_result_selector(ip_range)
        )
        return network_util

    @staticmethod
    def create(ctx: Context) -> "FakeNetworkUtil":
        return FakeNetworkUtil._create_fake(FakePrinter.create(ctx), dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())

    def register_scan_result(self, ip_range: str, expected_output: dict):
        """
        Register response dict of structure:
        {"ip_address": 1.1.1.1, "hostname": test-name, "status": Up/Unknown}
        """
        self.registered_scan_results[ip_range] = expected_output

    def _scan_result_selector(self, ip_range: str) -> str:
        for key, value in self.registered_scan_results.items():
            if ip_range == key:
                return value
        raise LookupError("Fake network util scan result is not defined. ip_range: " + ip_range)
