#!/usr/bin/env python3

import unittest
from typing import Callable
from unittest import mock

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.network import NetworkUtil
from provisioner_shared.components.runtime.utils.printer_fakes import FakePrinter
from provisioner_shared.components.runtime.utils.progress_indicator_fakes import FakeProgressIndicator
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_shared/components/runtime/utils/network_test.py
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
    @mock.patch("nmap3.NmapHostDiscovery.nmap_no_portscan", side_effect=[LAN_NOPORT_SCAN_TEST_RESULT])
    @mock.patch("nmap3.Nmap.nmap_list_scan", side_effect=[LAN_LIST_SCAN_TEST_RESULT])
    def test_run_get_and_parse_all_lan_network_devices_with_up_state(
        self,
        nmap_list_scan_call: mock.MagicMock,
        nmap_no_portscan_call: mock.MagicMock,
    ):
        env = TestEnv.create(ctx=Context.create(non_interactive=True))
        fake_printer = FakePrinter.create(env.get_context())
        fake_p_indicator = FakeProgressIndicator.create(env.get_context())

        def long_running_process_fn_call_1(call, desc_run, desc_end):
            self.assertEqual(desc_run, "Running LAN port scanning")
            self.assertEqual(desc_end, "LAN port scanning finished")
            return call()

        fake_p_indicator.get_status().on(
            "long_running_process_fn", Callable, str, str
        ).side_effect = long_running_process_fn_call_1

        def long_running_process_fn_call_2(call, desc_run, desc_end):
            self.assertEqual(desc_run, "Running LAN list scanning")
            self.assertEqual(desc_end, "LAN list scanning finished")
            return call()

        fake_p_indicator.get_status().on(
            "long_running_process_fn", Callable, str, str
        ).side_effect = long_running_process_fn_call_2

        network_util: NetworkUtil = NetworkUtil.create(env.get_context(), fake_printer, fake_p_indicator)
        devices_result_dict = network_util.get_all_lan_network_devices_fn(EXPECTED_IP_RANGE)

        Assertion.expect_call_argument(self, nmap_list_scan_call, arg_name="target", expected_value=EXPECTED_IP_RANGE)
        Assertion.expect_call_argument(self, nmap_no_portscan_call, arg_name="target", expected_value=EXPECTED_IP_RANGE)

        # Compare two dictionaries after merge
        noport_scan_result_dict = {
            "192.168.1.1": {"ip_address": "192.168.1.1", "hostname": "Network-Util-Test-01", "status": "up"}
        }
        # list_scan_result_dict = {
        #     "192.168.1.2": {"ip_address": "192.168.1.2", "hostname": "Network-Util-Test-02", "status": "unknown"},
        #     "192.168.1.3": {"ip_address": "192.168.1.3", "hostname": "No-Status-Scan-Item-01", "status": "unknown"},
        # }

        # self.assertEqual(noport_scan_result_dict | list_scan_result_dict, devices_result_dict)
        self.assertEqual(noport_scan_result_dict, devices_result_dict)
