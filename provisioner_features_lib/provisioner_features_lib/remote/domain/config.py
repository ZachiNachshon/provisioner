#!/usr/bin/env python3

from enum import Enum

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
        if other.remote.hosts:
            self.remote.hosts = other.remote.hosts

        if other.remote.lan_scan.ip_discovery_range:
            self.remote.lan_scan.ip_discovery_range = other.remote.lan_scan.ip_discovery_range

        return self
    
    def _parse_node_block(self, node_block: dict):
        if "gw_ip_address" in node_block:
            self.gw_ip_address = node_block["gw_ip_address"]
        if "dns_ip_address" in node_block:
            self.dns_ip_address = node_block["dns_ip_address"]

    def _parse_remote_block(self, remote_block: dict):
        if "hosts" in remote_block:
            hosts_block = remote_block["hosts"]
            self.remote.hosts = {}
            for host in hosts_block:
                if "name" in host and "address" in host:
                    auth_block = self._parse_host_auth_block(host)
                    h = RemoteConfig.Host(host["name"], host["address"], auth_block)
                    self.remote.hosts[host["name"]] = h
                else:
                    print("Bad hosts configuration, please check YAML file")

        if "lan_scan" in remote_block:
            lan_scan_block = remote_block["lan_scan"]
            if "ip_discovery_range" in lan_scan_block:
                self.remote.lan_scan.ip_discovery_range = lan_scan_block["ip_discovery_range"]

    def _parse_host_auth_block(self, host_block: dict) -> "RemoteConfig.Host.Auth":
        auth_obj = RemoteConfig.Host.Auth()
        if "auth" in host_block:
            auth_block = host_block["auth"]
            if "username" in auth_block:
                auth_obj.username = auth_block["username"]
            if "password" in auth_block:
                auth_obj.password = auth_block["password"]
            if "ssh_private_key_file_path" in auth_block:
                auth_obj.ssh_private_key_file_path = auth_block["ssh_private_key_file_path"]

        return auth_obj
    
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

        name: str
        address: str
        auth: Auth

        def __init__(self, name: str = None, address: str = None, auth: Auth = Auth()) -> None:
            self.name = name
            self.address = address
            self.auth = auth

    class LanScan:
        ip_discovery_range: str

        def __init__(self, ip_discovery_range: str = None) -> None:
            self.ip_discovery_range = ip_discovery_range

    lan_scan: LanScan
    hosts: dict[str, Host]
