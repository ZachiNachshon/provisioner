#!/usr/bin/env python3

import unittest
from unittest import mock

from ..infra.context import Context
from ..utils.io_utils_fakes import FakeIOUtils
from ..utils.network import NetworkUtil
from ..utils.os import MAC_OS, OsArch
from ..utils.printer_fakes import FakePrinter
from ..utils.process import Process
from ..utils.process_fakes import FakeProcess

LAN_NOPORT_SCAN_TEST_RESULT = {
    "192.168.1.1": {
        "osmatch": {},
        "ports": [],
        "hostname": [{"name": "Network-Util-Test-01", "type": "PTR"}],
        "macaddress": "null",
        "state": {"state": "up", "reason": "conn-refused", "reason_ttl": "0"},
    },
    "192.168.1.4": {
        "osmatch": {},
        "ports": [],
        "hostname": [],
        "macaddress": "null",
        "state": {
            "state": "unknown",
        },
    },
}

LAN_LIST_SCAN_TEST_RESULT = {
    "192.168.1.2": {
        "osmatch": {},
        "ports": [],
        "hostname": [{"name": "Network-Util-Test-02", "type": "PTR"}],
        "macaddress": "null",
        "state": {"state": "unknown", "reason": "conn-refused", "reason_ttl": "0"},
    },
    "192.168.1.3": {
        "osmatch": {},
        "ports": [],
        "hostname": [{"name": "No-Status-Scan-Item-01", "type": "PTR"}],
        "macaddress": "null",
    },
}


class FakeCollaborators:
    def __init__(self, ctx: Context) -> None:
        print("Creating fake network test collaborators...")
        self.io = FakeIOUtils.create()
        self.process = FakeProcess.create(ctx)


class NetworkTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def _run_get_all_lan_network_devices(
        self, nmap_list_scan_call: mock.MagicMock, nmap_no_portscan_call: mock.MagicMock, show_progress: bool
    ):

        ip_range = "192.168.1.1"
        os_arch = OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")
        ctx = Context.create(os_arch=os_arch)
        fake_printer = FakePrinter.create(ctx)
        network = NetworkUtil.create(ctx, fake_printer)

        devices = network.get_all_lan_network_devices_fn(ip_range=ip_range, show_progress=show_progress)

        self.assertEqual(1, nmap_list_scan_call.call_count)
        self.assertEqual(1, nmap_no_portscan_call.call_count)

        nmap_list_scan_call_kwargs = nmap_list_scan_call.call_args.kwargs
        self.assertEqual(ip_range, nmap_list_scan_call_kwargs["target"])

        nmap_no_portscan_call_kwargs = nmap_no_portscan_call.call_args.kwargs
        self.assertEqual(ip_range, nmap_no_portscan_call_kwargs["target"])

        # Compare two dictionaries after merge
        noport_scan_result_dict = {
            "192.168.1.1": {"ip_address": "192.168.1.1", "hostname": "Network-Util-Test-01", "status": "Up"}
        }
        list_scan_result_dict = {
            "192.168.1.2": {"ip_address": "192.168.1.2", "hostname": "Network-Util-Test-02", "status": "Unknown"},
            "192.168.1.3": {"ip_address": "192.168.1.3", "hostname": "No-Status-Scan-Item-01", "status": "Unknown"},
        }
        self.assertEqual(noport_scan_result_dict | list_scan_result_dict, devices)

    @mock.patch("nmap3.NmapHostDiscovery.nmap_no_portscan", side_effect=[LAN_NOPORT_SCAN_TEST_RESULT])
    @mock.patch("nmap3.Nmap.nmap_list_scan", side_effect=[LAN_LIST_SCAN_TEST_RESULT])
    def test_get_all_lan_network_devices(
        self, nmap_list_scan_call: mock.MagicMock, nmap_no_portscan_call: mock.MagicMock
    ):

        self._run_get_all_lan_network_devices(nmap_list_scan_call, nmap_no_portscan_call, show_progress=False)

    @mock.patch("nmap3.NmapHostDiscovery.nmap_no_portscan", side_effect=[LAN_NOPORT_SCAN_TEST_RESULT])
    @mock.patch("nmap3.Nmap.nmap_list_scan", side_effect=[LAN_LIST_SCAN_TEST_RESULT])
    def test_get_all_lan_network_devices_with_progress(
        self, nmap_list_scan_call: mock.MagicMock, nmap_no_portscan_call: mock.MagicMock
    ):

        self._run_get_all_lan_network_devices(nmap_list_scan_call, nmap_no_portscan_call, show_progress=True)
