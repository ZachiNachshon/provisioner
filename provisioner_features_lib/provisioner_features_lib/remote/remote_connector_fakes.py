#!/usr/bin/env python3

from typing import Callable

from python_core_lib.runner.ansible.ansible_runner import AnsibleHost

from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)


class TestDataRemoteConnector:

    TEST_DATA_SSH_USERNAME_1 = "test-username-1"
    TEST_DATA_SSH_USERNAME_2 = "test-username-2"
    TEST_DATA_SSH_PASSWORD_1 = "test-password-1"
    TEST_DATA_SSH_PASSWORD_2 = "test-password-2"
    TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1 = "test-ssh-private-key-file-path-1"
    TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_2 = "test-ssh-private-key-file-path-2"
    TEST_DATA_SSH_HOSTNAME_1 = "test-hostname-1"
    TEST_DATA_SSH_IP_ADDRESS_1 = "test-ip-address-1"
    TEST_DATA_SSH_HOSTNAME_2 = "test-hostname-2"
    TEST_DATA_SSH_IP_ADDRESS_2 = "test-ip-address-2"
    TEST_DATA_ANSIBLE_HOST_1 = AnsibleHost(
        host=TEST_DATA_SSH_HOSTNAME_1,
        ip_address=TEST_DATA_SSH_IP_ADDRESS_1,
        username=TEST_DATA_SSH_USERNAME_1,
        password=TEST_DATA_SSH_PASSWORD_1,
        ssh_private_key_file_path=TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1,
    )
    TEST_DATA_ANSIBLE_HOST_2 = AnsibleHost(
        host=TEST_DATA_SSH_HOSTNAME_2,
        ip_address=TEST_DATA_SSH_IP_ADDRESS_2,
        username=TEST_DATA_SSH_USERNAME_2,
        password=TEST_DATA_SSH_PASSWORD_2,
        ssh_private_key_file_path=TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_2,
    )

    TEST_DATA_SSH_ANSIBLE_HOSTS = [TEST_DATA_ANSIBLE_HOST_1, TEST_DATA_ANSIBLE_HOST_2]
    TEST_DATA_DHCP_GW_IP_ADDRESS = "test-gw-ip-address"
    TEST_DATA_DHCP_DNS_IP_ADDRESS = "test-dns-ip-address"
    TEST_DATA_DHCP_STATIC_IP_ADDRESS = "test-static-ip-address"

    @staticmethod
    def create_fake_ssh_conn_info_fn() -> Callable[..., SSHConnectionInfo]:
        def create_fn(*any) -> SSHConnectionInfo:
            return SSHConnectionInfo(ansible_hosts=TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS)

        return create_fn

    @staticmethod
    def create_fake_get_dhcpcd_configure_info_fn() -> Callable[..., DHCPCDConfigurationInfo]:
        def create_fn(*any) -> DHCPCDConfigurationInfo:
            return DHCPCDConfigurationInfo(
                gw_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS,
                dns_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS,
                static_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
            )

        return create_fn
