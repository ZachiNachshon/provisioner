#!/usr/bin/env python3

from enum import Enum
from typing import List


# TODO:
# Tests are failing when not using default for class variables, need to investigate why
# When using defaults, all tests pass - need to check the dot-notations and use hasattr()

from loguru import logger
from provisioner.domain.serialize import SerializationBase

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

class LanScan(SerializationBase):
    ip_discovery_range: str = ""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "LanScan") -> SerializationBase:
        if hasattr(other, "ip_discovery_range") and len(other.ip_discovery_range) > 0:
            self.ip_discovery_range = other.ip_discovery_range
        return self

    def _try_parse_config(self, dict_obj: dict) -> None:
        if "ip_discovery_range" in dict_obj:
            self.ip_discovery_range = dict_obj["ip_discovery_range"]
    
class Auth(SerializationBase):
    username: str = ""
    password: str = ""
    ssh_private_key_file_path: str = ""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "Auth") -> SerializationBase:
        if hasattr(other, "username") and len(other.username) > 0:
            self.username = other.username
        if hasattr(other, "password") and len(other.password) > 0:
            self.password = other.password
        if hasattr(other, "ssh_private_key_file_path") and len(other.ssh_private_key_file_path) > 0:
            self.ssh_private_key_file_path = other.ssh_private_key_file_path
        return self
    
    def _try_parse_config(self, dict_obj: dict) -> None:
        if "username" in dict_obj:
            self.username = dict_obj["username"]
        if "password" in dict_obj:
            self.password = dict_obj["password"]
        if "ssh_private_key_file_path" in dict_obj:
            self.ssh_private_key_file_path = dict_obj["ssh_private_key_file_path"]

class Host(SerializationBase):
    name: str = ""
    address: str = ""
    auth: Auth = Auth({})

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "Host") -> SerializationBase:
        # Hosts aren't mergable, they are all or nothing
        return self

    def _try_parse_config(self, dict_obj: dict) -> None:
        if "name" in dict_obj:
            self.name = dict_obj["name"]
        if "address" in dict_obj:
            self.address = dict_obj["address"]
        if "auth" in dict_obj:
            self.auth = Auth(dict_obj["auth"])

class RemoteConfig(SerializationBase):
    lan_scan: LanScan = LanScan({})
    hosts: List[Host] = []
    
    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "RemoteConfig") -> SerializationBase:
        # Hosts config are all or nothing, if partial config is provided, user overrides won't apply
        if hasattr(other, "hosts"):
            self.hosts = []
            for other_host in other.hosts:
                if not hasattr(other_host, "name") and not hasattr(other_host, "address") and not hasattr(other_host, "auth"):
                    msg = f"Partial host config identified, missing a name, address or auth, please check YAML file !"
                    print(msg)
                    logger.error(msg)
                else:
                    new_host = Host({})
                    new_host.name = other_host.name
                    new_host.address = other_host.address
                    new_host.auth = other_host.auth if other_host.auth is not None else Auth()
                    self.hosts.append(new_host)

        if hasattr(other, "lan_scan"):
            self.lan_scan = self.lan_scan if self.lan_scan is not None else LanScan()
            self.lan_scan.merge(other.lan_scan)

        return self
    
    def _try_parse_config(self, dict_obj: dict) -> None:
        if "hosts" in dict_obj:
            hosts_block = dict_obj["hosts"]
            self.hosts = []
            for host_block in hosts_block:
                if "name" not in host_block or "address" not in host_block or "auth" not in host_block:
                    msg = f"Partial host config identified, missing a name, address or auth, please check YAML file !"
                    print(msg)
                    logger.error(msg)
                else:
                    new_host = Host(host_block)
                    self.hosts.append(new_host)

        if "lan_scan" in dict_obj:
            self.lan_scan = LanScan(dict_obj["lan_scan"])

    def to_hosts_dict(self) -> dict[str, "Host"]:
        return {host.name: host for host in self.hosts}
    