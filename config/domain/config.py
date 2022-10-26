#!/usr/bin/env python3

from external.python_scripts_lib.python_scripts_lib.domain.serialize import (
    SerializationBase,
)

class RemoteConfig:

    class Host:
        name: str
        address: str

        def __init__(self, name: str, address: str) -> None:
            self.name = name
            self.address = address

    class LanScan:
        ip_discovery_range: str = None

    class Auth:
        node_username: str = None
        node_password: str = None
        ssh_private_key_file_path: str = None
    
    lan_scan: LanScan = LanScan()
    auth: Auth = Auth()
    hosts: dict[str, Host] = None
    

class AnchorConfig:

    class GitHubConfig:
        organization: str = None
        repository: str = None
        branch: str = None
        github_access_token: str = None

    github: GitHubConfig = GitHubConfig()

class DummyConfig:

    class HelloWorldConfig:
        username: str = None

    hello_world: HelloWorldConfig = HelloWorldConfig()

class RpiConfig:

    class RpiOsConfig:
        active_system: str = None
        download_url_32bit: str = None
        download_url_64bit: str = None
        download_path: str = None

    class RpiNetworkConfig:
        gw_ip_address: str = None
        dns_ip_address: str = None

    os: RpiOsConfig = RpiOsConfig()
    network: RpiNetworkConfig = RpiNetworkConfig()

class ProvisionerConfig(SerializationBase):

    remote: RemoteConfig = RemoteConfig()
    anchor: AnchorConfig = AnchorConfig()
    dummmy: DummyConfig = DummyConfig()
    rpi: RpiConfig = RpiConfig()

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

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
                    h = RemoteConfig.Host(host["name"], host["address"])
                    self.remote.hosts[host["name"]] = h
                else:
                    print("Bad hosts configuration, please check YAML file")

        if "lan_scan" in remote_block:
            lan_scan_block = remote_block["lan_scan"]
            if "ip_discovery_range" in lan_scan_block:
                self.remote.lan_scan.ip_discovery_range = lan_scan_block["ip_discovery_range"]

        if "auth" in remote_block:
            auth_block = remote_block["auth"]
            if "username" in auth_block:
                self.remote.auth.node_username = auth_block["username"]
            if "password" in auth_block:
                self.remote.auth.node_password = auth_block["password"]
            if "ssh_private_key_file_path" in auth_block:
                self.remote.auth.ssh_private_key_file_path = auth_block["ssh_private_key_file_path"]

    def _parse_anchor_block(self, anchor_block: dict):
        if "github" in anchor_block:
            github_block = anchor_block["github"]
            if "organization" in github_block:
                self.anchor.github.organization = github_block["organization"]
            if "repository" in github_block:
                self.anchor.github.repository = github_block["repository"]
            if "branch" in github_block:
                self.anchor.github.branch = github_block["branch"]
            if "github_access_token" in github_block:
                self.anchor.github.github_access_token = github_block["github_access_token"]

    def _parse_dummy_block(self, dummy_block: dict):
        if "hello_world" in dummy_block:
            hello_world_block = dummy_block["hello_world"]
            if "username" in hello_world_block:
                self.dummmy.hello_world.username = hello_world_block["username"]

    def _parse_rpi_block(self, rpi_block: dict):
        if "os" in rpi_block:
            os_block = rpi_block["os"]
            if "raspbian" in os_block:
                raspbian_block = os_block["raspbian"]
                if "download_path" in raspbian_block:
                    self.rpi.os.download_path = raspbian_block["download_path"]
                if "active_system" in raspbian_block:
                    self.rpi.os.active_system = raspbian_block["active_system"]
                if "download_url" in raspbian_block:
                    download_url_block = raspbian_block["download_url"]
                    if "32bit" in download_url_block:
                        self.rpi.os.download_url_32bit = download_url_block["32bit"]
                    if "64bit" in download_url_block:
                        self.rpi.os.download_url_64bit = download_url_block["64bit"]

        if "network" in rpi_block:
            network_block = rpi_block["network"]
            if "gw_ip_address" in network_block:
                self.rpi.network.gw_ip_address = network_block["gw_ip_address"]
            if "dns_ip_address" in network_block:
                self.rpi.network.dns_ip_address = network_block["dns_ip_address"]

    def _try_parse_config(self, dict_obj: dict):
        provisioner_data = dict_obj["provisioner"]
        if "remote" in provisioner_data:
            self._parse_remote_block(provisioner_data["remote"])
        if "anchor" in provisioner_data:
            self._parse_anchor_block(provisioner_data["anchor"])
        if "dummy" in provisioner_data:
            self._parse_dummy_block(provisioner_data["dummy"])
        if "rpi" in provisioner_data:
            self._parse_rpi_block(provisioner_data["rpi"])

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        if other.remote.hosts:
            self.remote.hosts = other.remote.hosts

        if other.remote.lan_scan.ip_discovery_range:
            self.remote.lan_scan.ip_discovery_range = other.remote.lan_scan.ip_discovery_range

        if other.remote.auth.node_username:
            self.remote.auth.node_username = other.remote.auth.node_username
        if other.remote.auth.node_password:
            self.remote.auth.node_password = other.remote.auth.node_password
        if other.remote.auth.ssh_private_key_file_path:
            self.remote.auth.ssh_private_key_file_path = other.remote.auth.ssh_private_key_file_path

        if other.anchor.github.organization:
            self.anchor.github.organization = other.anchor.github.organization
        if other.anchor.github.repository:
            self.anchor.github.repository = other.anchor.github.repository
        if other.anchor.github.branch:
            self.anchor.github.branch = other.anchor.github.branch
        if other.anchor.github.github_access_token:
            self.anchor.github.github_access_token = other.anchor.github.github_access_token

        if other.dummmy.hello_world.username:
            self.dummmy.hello_world.username = other.dummmy.hello_world.username

        if other.rpi.os.active_system:
            self.rpi.os.active_system = other.rpi.os.active_system
        if other.rpi.os.download_path:
            self.rpi.os.download_path = other.rpi.os.download_path
        if other.rpi.os.download_url_32bit:
            self.rpi.os.download_url_32bit = other.rpi.os.download_url_32bit
        if other.rpi.os.download_url_64bit:
            self.rpi.os.download_url_64bit = other.rpi.os.download_url_64bit

        if other.rpi.network.gw_ip_address:
            self.rpi.network.gw_ip_address = other.rpi.network.gw_ip_address
        if other.rpi.network.dns_ip_address:
            self.rpi.network.dns_ip_address = other.rpi.network.dns_ip_address

        return self

    def get_os_raspbian_download_url(self):
        if self.rpi.os.active_system == "64bit":
            return self.rpi.os.download_url_64bit
        return self.rpi.os.download_url_32bit
