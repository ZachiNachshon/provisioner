#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.network import NetworkUtil

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest python_core_lib/utils/network_test.py
#
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

EXPECTED_IP_RANGE = "192.168.1.1"


class NetworkTestShould(unittest.TestCase):
    def _run_get_all_lan_network_devices(
        self, nmap_list_scan_call: mock.MagicMock, nmap_no_portscan_call: mock.MagicMock, show_progress: bool
    ):
        env = TestEnv.create()
        network_util = NetworkUtil.create(env.get_context(), env.get_collaborators().printer())
        devices_result_dict = network_util.get_all_lan_network_devices_fn(
            ip_range=EXPECTED_IP_RANGE, show_progress=show_progress
        )
        Assertion.expect_call_argument(self, nmap_list_scan_call, arg_name="target", expected_value=EXPECTED_IP_RANGE)
        Assertion.expect_call_argument(self, nmap_no_portscan_call, arg_name="target", expected_value=EXPECTED_IP_RANGE)

        # Compare two dictionaries after merge
        noport_scan_result_dict = {
            "192.168.1.1": {"ip_address": "192.168.1.1", "hostname": "Network-Util-Test-01", "status": "Up"}
        }
        list_scan_result_dict = {
            "192.168.1.2": {"ip_address": "192.168.1.2", "hostname": "Network-Util-Test-02", "status": "Unknown"},
            "192.168.1.3": {"ip_address": "192.168.1.3", "hostname": "No-Status-Scan-Item-01", "status": "Unknown"},
        }
        self.assertEqual(noport_scan_result_dict | list_scan_result_dict, devices_result_dict)

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
