#!/usr/bin/env python3


from provisioner_shared.components.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsibleHost


class TestDataRemoteConnector:

    TEST_DATA_SSH_USERNAME_1 = "test-username-1"
    TEST_DATA_SSH_USERNAME_2 = "test-username-2"
    TEST_DATA_SSH_PASSWORD_1 = "test-password-1"
    TEST_DATA_SSH_PASSWORD_2 = "test-password-2"
    TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1 = "test-ssh-private-key-file-path-1"
    TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_2 = "test-ssh-private-key-file-path-2"
    TEST_DATA_SSH_HOSTNAME_1 = "test-hostname-1"
    TEST_DATA_SSH_IP_ADDRESS_1 = "test-ip-address-1"
    TEST_DATA_SSH_PORT_1 = 2222
    TEST_DATA_SSH_PORT_2 = 2233
    TEST_DATA_SSH_HOSTNAME_2 = "test-hostname-2"
    TEST_DATA_SSH_IP_ADDRESS_2 = "test-ip-address-2"
    TEST_DATA_ANSIBLE_HOST_1 = AnsibleHost(
        host=TEST_DATA_SSH_HOSTNAME_1,
        ip_address=TEST_DATA_SSH_IP_ADDRESS_1,
        port=TEST_DATA_SSH_PORT_1,
        username=TEST_DATA_SSH_USERNAME_1,
        password=TEST_DATA_SSH_PASSWORD_1,
        ssh_private_key_file_path=TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1,
    )
    TEST_DATA_ANSIBLE_HOST_2 = AnsibleHost(
        host=TEST_DATA_SSH_HOSTNAME_2,
        ip_address=TEST_DATA_SSH_IP_ADDRESS_2,
        port=TEST_DATA_SSH_PORT_2,
        username=TEST_DATA_SSH_USERNAME_2,
        password=TEST_DATA_SSH_PASSWORD_2,
        ssh_private_key_file_path=TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_2,
    )

    TEST_DATA_SSH_ANSIBLE_HOSTS = [TEST_DATA_ANSIBLE_HOST_1, TEST_DATA_ANSIBLE_HOST_2]
    TEST_DATA_DHCP_GW_IP_ADDRESS = "test-gw-ip-address"
    TEST_DATA_DHCP_DNS_IP_ADDRESS = "test-dns-ip-address"
    TEST_DATA_DHCP_STATIC_IP_ADDRESS = "test-static-ip-address"

    @staticmethod
    def create_fake_ssh_conn_info() -> SSHConnectionInfo:
        return SSHConnectionInfo(ansible_hosts=TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS)

    @staticmethod
    def create_fake_get_dhcpcd_configure_info() -> DHCPCDConfigurationInfo:
        return DHCPCDConfigurationInfo(
            gw_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS,
            dns_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS,
            static_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
        )
