#!/usr/bin/env python3

from typing import Optional

import nmap3
from loguru import logger
from nmap3 import NmapHostDiscovery

from provisioner.infra.context import Context
from provisioner.utils.printer import Printer
from provisioner.utils.progress_indicator import ProgressIndicator


class NetworkUtil:

    _dry_run: bool = None
    _verbose: bool = None

    _nmap = None
    _host_discovery = None
    _progress_indicator = None

    def __init__(self, printer: Printer, progress_indicator: ProgressIndicator, dry_run: bool, verbose: bool):
        self._dry_run = dry_run
        self._verbose = verbose
        self._printer = printer
        self._progress_indicator = progress_indicator
        self._nmap = nmap3.Nmap()
        self._host_discovery = NmapHostDiscovery()

    @staticmethod
    def create(ctx: Context, printer: Printer, progress_indicator: ProgressIndicator) -> "NetworkUtil":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating network util (dry_run: {dry_run}, verbose: {verbose})...")
        return NetworkUtil(printer, progress_indicator, dry_run, verbose)

    def _is_host_state_up(self, ip_scan_result: dict) -> bool:
        if "state" in ip_scan_result and ip_scan_result["state"]["state"]:
            state = ip_scan_result["state"]["state"]
            return state in ["up"]
        return False

    def _try_read_hostname(self, ip_scan_result: dict) -> str:
        if "hostname" in ip_scan_result and len(ip_scan_result["hostname"]) > 0:
            hostname_dict = ip_scan_result["hostname"]
            # Always take the 1st item, if found
            for name in hostname_dict:
                if name["name"]:
                    return name["name"]
        return None

    def _generate_scanned_item_desc(self, ip_addr: str, hostname: str, status: str) -> dict:
        return {"ip_address": ip_addr, "hostname": hostname, "status": status}

    def _extract_valid_scanned_items(self, scanned_dict: dict) -> dict[str, dict]:
        response = {}
        for ip_addr in scanned_dict:
            ip_scan_result = scanned_dict[ip_addr]
            if len(ip_scan_result) > 0:
                hostname = self._try_read_hostname(ip_scan_result)
                if hostname:
                    status = "Up" if self._is_host_state_up(ip_scan_result) else "Unknown"
                    response[ip_addr] = self._generate_scanned_item_desc(ip_addr, hostname, status)
        return response

    def _get_all_lan_network_devices(self, ip_range: str, filter_str: Optional[str] = None) -> dict[str, dict]:
        """
        Every nmap response dict structure is as follows:
        {
            '192.168.1.0': {
                "osmatch":
                {},
                "ports":
                [],
                "hostname":
                [
                    {
                        "name": "Google-Home-Mini",
                        "type": "PTR"
                    }
                ],
                "macaddress": null,
                "state":
                {
                    "state": "up",
                    "reason": "conn-refused",
                    "reason_ttl": "0"
                }
            }
            ...
        }
        """
        result_dict = {}

        if self._dry_run:
            return result_dict

        port_scan_result_dict = None
        port_scan_result_dict = self._progress_indicator.get_status().long_running_process_fn(
            call=lambda: self._host_discovery.nmap_no_portscan(target=ip_range),
            desc_run="Running LAN port scanning",
            desc_end="LAN port scanning finished",
        )

        result_dict.update(self._extract_valid_scanned_items(port_scan_result_dict))

        list_scan_result_dict = None
        list_scan_result_dict = self._progress_indicator.get_status().long_running_process_fn(
            call=lambda: self._nmap.nmap_list_scan(target=ip_range),
            desc_run="Running LAN list scanning",
            desc_end="LAN list scanning finished",
        )

        result_dict.update(self._extract_valid_scanned_items(list_scan_result_dict))

        return result_dict

    get_all_lan_network_devices_fn = _get_all_lan_network_devices
