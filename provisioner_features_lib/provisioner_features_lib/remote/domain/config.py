#!/usr/bin/env python3

from enum import Enum
from typing import List

from loguru import logger
from provisioner.domain.serialize import SerializationBase


class RunEnvironment(str, Enum):
    Local = "Local"
    Remote = "Remote"

    @staticmethod
    def from_str(label):
        if label in ("Local"):
            return RunEnvironment.Local
        elif label in ("Remote"):
            return RunEnvironment.Remote
        else:
            raise NotImplementedError(f"RunEnvironment enum does not support label '{label}'")


class RemoteConfig(SerializationBase):
    """
    Configuration structure -

    remote:
        hosts:
        - name: kmaster
          address: 192.168.1.200
          auth:
            username: pi
            password: raspberry

        - name: knode1
          address: 192.168.1.201
          auth:
            username: pi
            ssh_private_key_file_path: /path/to/unknown

        - name: knode2
          address: 192.168.1.202
          auth:
            username: pi

        lan_scan:
            ip_discovery_range: 192.168.1.1/24
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "remote" in dict_obj:
            self._parse_remote_block(dict_obj["remote"])

    def merge(self, other: "RemoteConfig") -> SerializationBase:
        # Hosts config are all or nothing, if partial config is provided, user overrides won't apply
        if hasattr(other, "hosts"):
            for host in other.hosts:
                if not hasattr(host, "name") and \
                not hasattr(host, "address") and \
                not hasattr(host, "auth"):
                    logger.error(f"Partial hosts config identified, missing a name, address or auth, user overrides won't apply !")
            self.hosts = other.hosts

        if hasattr(other, "lan_scan"):
            if hasattr(other.lan_scan, "ip_discovery_range"):
                self.lan_scan.ip_discovery_range = other.lan_scan.ip_discovery_range

        return self

    def to_hosts_dict(self) -> dict[str, "RemoteConfig.Host"]:
        return {host.name: host for host in self.hosts}
    
    def _parse_remote_block(self, remote_block: dict):
        if "hosts" in remote_block:
            hosts_block = remote_block["hosts"]
            self.hosts = []
            for host in hosts_block:
                if "name" in host and "address" in host:
                    h = RemoteConfig.Host()
                    h.parse(host)
                    self.hosts.append(h)
                else:
                    print("Bad hosts configuration, please check YAML file")

        if "lan_scan" in remote_block:
            self.lan_scan = RemoteConfig.LanScan()
            lan_scan_block = remote_block["lan_scan"]
            if "ip_discovery_range" in lan_scan_block:
                self.lan_scan.ip_discovery_range = lan_scan_block["ip_discovery_range"]

    class Host:
        class Auth:
            username: str
            password: str
            ssh_private_key_file_path: str

            def __init__(
                self, username: str = None, password: str = None, ssh_private_key_file_path: str = None
            ) -> None:
                self.username = username
                self.password = password
                self.ssh_private_key_file_path = ssh_private_key_file_path

            def parse(self, auth_block: dict) -> None:
                if "username" in auth_block:
                    self.username = auth_block["username"]
                if "password" in auth_block:
                    self.password = auth_block["password"]
                if "ssh_private_key_file_path" in auth_block:
                    self.ssh_private_key_file_path = auth_block["ssh_private_key_file_path"]

        name: str
        address: str
        auth: Auth

        def __init__(self, name: str = None, address: str = None, auth: Auth = Auth()) -> None:
            self.name = name
            self.address = address
            self.auth = auth

        def parse(self, host_block: dict) -> None:
            if "name" in host_block:
                self.name = host_block["name"]
            if "address" in host_block:
                self.address = host_block["address"]
            if "auth" in host_block:
                self.auth = RemoteConfig.Host.Auth()
                self.auth.parse(host_block["auth"])

    class LanScan:
        ip_discovery_range: str

        def __init__(self, ip_discovery_range: str = None) -> None:
            self.ip_discovery_range = ip_discovery_range

    lan_scan: LanScan
    hosts: List[Host]
