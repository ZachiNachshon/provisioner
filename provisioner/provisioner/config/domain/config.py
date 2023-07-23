#!/usr/bin/env python3

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.remote.domain.config import RemoteConfig
from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.utils.package_loader import PackageLoader

PLUGIN_EXAMPLES_CONFIG_MODULE_NAME = "provisioner_examples_plugin.domain.config"
PLUGIN_SINGLE_BOARD_CONFIG_MODULE_NAME = "provisioner_single_board_plugin.config.domain.config"

pkg_loader = PackageLoader.create()


def is_examples_plugin_loaded() -> bool:
    return pkg_loader.is_module_loaded_fn(PLUGIN_EXAMPLES_CONFIG_MODULE_NAME)


def is_single_board_plugin_loaded() -> bool:
    return pkg_loader.is_module_loaded_fn(PLUGIN_SINGLE_BOARD_CONFIG_MODULE_NAME)


class ProvisionerConfig(SerializationBase):
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
                    auth_block = self._parse_host_auth_block(host)
                    h = RemoteConfig.Host(host["name"], host["address"], auth_block)
                    self.remote.hosts[host["name"]] = h
                else:
                    print("Bad hosts configuration, please check YAML file")

        if "lan_scan" in remote_block:
            lan_scan_block = remote_block["lan_scan"]
            if "ip_discovery_range" in lan_scan_block:
                self.remote.lan_scan.ip_discovery_range = lan_scan_block["ip_discovery_range"]

    def _parse_host_auth_block(self, host_block: dict) -> RemoteConfig.Host.Auth:
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

    def _parse_anchor_block(self, anchor_block: dict):
        if "github" in anchor_block:
            github_block = anchor_block["github"]
            if "organization" in github_block:
                self.anchor.github.organization = github_block["organization"]
            if "repository" in github_block:
                self.anchor.github.repository = github_block["repository"]
            if "branch" in github_block:
                self.anchor.github.branch = github_block["branch"]
            if "git_access_token" in github_block:
                self.anchor.github.git_access_token = github_block["git_access_token"]

    def _parse_dummy_block(self, dummy_block: dict):
        if "hello_world" in dummy_block:
            hello_world_block = dummy_block["hello_world"]
            if "username" in hello_world_block:
                self.dummmy.hello_world.username = hello_world_block["username"]

    def _parse_single_board_block(self, single_board_block: dict):
        if "os" in single_board_block:
            os_block = single_board_block["os"]
            if "raspbian" in os_block:
                raspbian_block = os_block["raspbian"]
                if "download_path" in raspbian_block:
                    self.single_board.os.download_path = raspbian_block["download_path"]
                if "active_system" in raspbian_block:
                    self.single_board.os.active_system = raspbian_block["active_system"]
                if "download_url" in raspbian_block:
                    download_url_block = raspbian_block["download_url"]
                    if "32bit" in download_url_block:
                        self.single_board.os.download_url_32bit = download_url_block["32bit"]
                    if "64bit" in download_url_block:
                        self.single_board.os.download_url_64bit = download_url_block["64bit"]

        if "network" in single_board_block:
            network_block = single_board_block["network"]
            if "gw_ip_address" in network_block:
                self.single_board.network.gw_ip_address = network_block["gw_ip_address"]
            if "dns_ip_address" in network_block:
                self.single_board.network.dns_ip_address = network_block["dns_ip_address"]

    def _try_parse_config(self, dict_obj: dict):
        provisioner_data = dict_obj["provisioner"]
        if "remote" in provisioner_data:
            self._parse_remote_block(provisioner_data["remote"])
        if "anchor" in provisioner_data:
            self._parse_anchor_block(provisioner_data["anchor"])
        if "dummy" in provisioner_data and is_examples_plugin_loaded():
            self._parse_dummy_block(provisioner_data["dummy"])
        if "single_board" in provisioner_data and is_single_board_plugin_loaded():
            self._parse_single_board_block(provisioner_data["single_board"])

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        if other.remote.hosts:
            self.remote.hosts = other.remote.hosts

        if other.remote.lan_scan.ip_discovery_range:
            self.remote.lan_scan.ip_discovery_range = other.remote.lan_scan.ip_discovery_range

        if other.anchor.github.organization:
            self.anchor.github.organization = other.anchor.github.organization
        if other.anchor.github.repository:
            self.anchor.github.repository = other.anchor.github.repository
        if other.anchor.github.branch:
            self.anchor.github.branch = other.anchor.github.branch
        if other.anchor.github.git_access_token:
            self.anchor.github.git_access_token = other.anchor.github.git_access_token

        if other.dummmy.hello_world.username:
            self.dummmy.hello_world.username = other.dummmy.hello_world.username

        if other.single_board.os.active_system:
            self.single_board.os.active_system = other.single_board.os.active_system
        if other.single_board.os.download_path:
            self.single_board.os.download_path = other.single_board.os.download_path
        if other.single_board.os.download_url_32bit:
            self.single_board.os.download_url_32bit = other.single_board.os.download_url_32bit
        if other.single_board.os.download_url_64bit:
            self.single_board.os.download_url_64bit = other.single_board.os.download_url_64bit

        if other.single_board.network.gw_ip_address:
            self.single_board.network.gw_ip_address = other.single_board.network.gw_ip_address
        if other.single_board.network.dns_ip_address:
            self.single_board.network.dns_ip_address = other.single_board.network.dns_ip_address

        return self

    remote: RemoteConfig = RemoteConfig()
    anchor: AnchorConfig = AnchorConfig()

    dummmy = pkg_loader.create_instance_fn(module_name=PLUGIN_EXAMPLES_CONFIG_MODULE_NAME, type_name="DummyConfig")
    single_board = pkg_loader.create_instance_fn(
        module_name=PLUGIN_SINGLE_BOARD_CONFIG_MODULE_NAME, type_name="SingleBoardConfig"
    )
