#!/usr/bin/env python3

from typing import Optional

import nmap3
from loguru import logger
from nmap3 import NmapHostDiscovery

from ..infra.context import Context
from .printer import Printer


class NetworkUtil:

    _dry_run: bool = None
    _verbose: bool = None

    _nmap = None
    _host_discovery = None
    _printer = None

    def __init__(self, printer: Printer, dry_run: bool, verbose: bool):
        self._dry_run = dry_run
        self._verbose = verbose
        self._printer = printer
        self._nmap = nmap3.Nmap()
        self._host_discovery = NmapHostDiscovery()

    @staticmethod
    def create(ctx: Context, printer: Printer) -> "NetworkUtil":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating network util (dry_run: {dry_run}, verbose: {verbose})...")
        return NetworkUtil(printer, dry_run, verbose)

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

    def _get_all_lan_network_devices(
        self, ip_range: str, filter_str: Optional[str] = None, show_progress: Optional[bool] = False
    ) -> dict[str, dict]:
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
        if show_progress:
            port_scan_result_dict = self._printer.progress_indicator.progress_bar.long_running_process_fn(
                call=lambda: self._host_discovery.nmap_no_portscan(target=ip_range),
                desc="Port Scanning",
                expected_time=301,
                increments=300,
            )
        else:
            self._printer.print_fn("Port Scanning...")
            port_scan_result_dict = self._host_discovery.nmap_no_portscan(target=ip_range)

        result_dict.update(self._extract_valid_scanned_items(port_scan_result_dict))

        list_scan_result_dict = None
        if show_progress:
            list_scan_result_dict = self._printer.progress_indicator.progress_bar.long_running_process_fn(
                call=lambda: self._nmap.nmap_list_scan(target=ip_range),
                desc="List Scanning",
                expected_time=51,
                increments=50,
            )
        else:
            self._printer.print_fn("List Scanning...")
            list_scan_result_dict = self._nmap.nmap_list_scan(target=ip_range)

        result_dict.update(self._extract_valid_scanned_items(list_scan_result_dict))

        return result_dict

    get_all_lan_network_devices_fn = _get_all_lan_network_devices
