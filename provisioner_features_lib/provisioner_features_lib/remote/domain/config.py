#!/usr/bin/env python3

from enum import Enum


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


class RemoteConfig:
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

    def __init__(self, lan_scan: LanScan = LanScan(), hosts: dict[str, Host] = None) -> None:
        self.lan_scan = lan_scan
        self.hosts = hosts

    lan_scan: LanScan
    hosts: dict[str, Host]
