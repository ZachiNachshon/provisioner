#!/usr/bin/env python3

from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import FailedToSerializeConfiguration
from external.python_scripts_lib.python_scripts_lib.domain.serialize import SerializationBase


class ProvisionerConfig(SerializationBase):

    active_system: str = None
    download_url_32bit: str = None
    download_url_64bit: str = None
    download_path: str = None

    ip_discovery_range: str = None
    node_username: str = None
    node_password: str = None
    gw_ip_address: str = None
    dns_ip_address: str = None

    ansible_playbook_path_configure_os: str = None
    ansible_playbook_path_configure_network: str = None
    ansible_playbook_path_wait_for_network: str = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _parse_os_block(self, os_block: dict):
        if "raspbian" in os_block:
            raspbian_block = os_block["raspbian"]
            if "download_path" in raspbian_block:
                self.download_path = raspbian_block["download_path"]
            if "active_system" in raspbian_block:
                self.active_system = raspbian_block["active_system"]
            if "download_url" in raspbian_block:
                download_url_block = raspbian_block["download_url"]
                if "32bit" in download_url_block:
                    self.download_url_32bit = download_url_block["32bit"]
                if "64bit" in download_url_block:
                    self.download_url_64bit = download_url_block["64bit"]

    def _parse_node_block(self, node_block: dict):
        if "ip_discovery_range" in node_block:
            self.ip_discovery_range = node_block["ip_discovery_range"]
        if "username" in node_block:
            self.node_username = node_block["username"]
        if "password" in node_block:
            self.node_password = node_block["password"]
        if "gw_ip_address" in node_block:
            self.gw_ip_address = node_block["gw_ip_address"]
        if "dns_ip_address" in node_block:
            self.dns_ip_address = node_block["dns_ip_address"]

    def _parse_ansible_block(self, ansible_block: dict):
        if "playbooks" in ansible_block:
            playbooks_block = ansible_block["playbooks"]
            if "configure_os" in playbooks_block:
                self.ansible_playbook_path_configure_os = playbooks_block["configure_os"]
            if "configure_network" in playbooks_block:
                self.ansible_playbook_path_configure_network = playbooks_block["configure_network"]
            if "wait_for_network" in playbooks_block:
                self.ansible_playbook_path_wait_for_network = playbooks_block["wait_for_network"]

    def _try_parse_config(self, dict_obj: dict):
        provisioner_data = dict_obj["provisioner"]
        if "rpi" in provisioner_data:
            if "os" in provisioner_data["rpi"]:
                os_block = provisioner_data["rpi"]["os"]
                self._parse_os_block(os_block)

            if "node" in provisioner_data["rpi"]:
                node_block = provisioner_data["rpi"]["node"]
                self._parse_node_block(node_block)

            if "ansible" in provisioner_data["rpi"]:
                ansible_block = provisioner_data["rpi"]["ansible"]
                self._parse_ansible_block(ansible_block)

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        if other.active_system:
            self.active_system = other.active_system

        if other.download_path:
            self.download_path = other.download_path

        if other.download_url_32bit:
            self.download_url_32bit = other.download_url_32bit

        if other.download_url_64bit:
            self.download_url_64bit = other.download_url_64bit

        if other.ip_discovery_range:
            self.ip_discovery_range = other.ip_discovery_range

        if other.node_username:
            self.node_username = other.node_username

        if other.node_password:
            self.node_password = other.node_password

        if other.gw_ip_address:
            self.gw_ip_address = other.gw_ip_address

        if other.dns_ip_address:
            self.dns_ip_address = other.dns_ip_address

        if other.ansible_playbook_path_configure_os:
            self.ansible_playbook_path_configure_os = other.ansible_playbook_path_configure_os

        if other.ansible_playbook_path_configure_network:
            self.ansible_playbook_path_configure_network = other.ansible_playbook_path_configure_network

        if other.ansible_playbook_path_wait_for_network:
            self.ansible_playbook_path_wait_for_network = other.ansible_playbook_path_wait_for_network

        return self

    def get_os_raspbian_download_url(self):
        if self.active_system == "64bit":
            return self.download_url_64bit
        return self.download_url_32bit
