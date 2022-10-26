#!/usr/bin/env python3

import os
import unittest
from unittest import mock

from typer.testing import CliRunner

from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
)
from rpi.main import app

TEST_CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
TEST_CONFIG_INTERNAL_PATH = "rpi/config.yaml"

runner = CliRunner()
#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os install
#  poetry run rpi --dry-run --verbose --auto-prompt os configure
#  poetry run rpi --dry-run --verbose --auto-prompt os network
#
# To run as a single test target:
#  poetry run coverage run -m pytest rpi/os/cli_test.py
#
class OsCliTestShould(unittest.TestCase):
    @mock.patch("rpi.os.install.RPiOsInstallCmd.run")
    def test_cli_install_runner_with_cli_args_success(self, run_call: mock.MagicMock) -> None:
        expected_image_download_url = "http://test.download.com"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "install",
                f"--image-download-url={expected_image_download_url}"
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_install_args = run_call_kwargs["args"]
        os_install_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_install_args)
        self.assertEqual(os_install_args.image_download_url, expected_image_download_url)

    @mock.patch("rpi.os.install.RPiOsInstallCmd.run")
    def test_cli_install_runner_with_config_args_success(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "install",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_install_args = run_call_kwargs["args"]
        os_install_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_install_args)
        self.assertEqual(os_install_args.image_download_url, 
        "https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2022-01-28/2022-01-28-raspios-bullseye-arm64-lite.zip")

    @mock.patch("rpi.os.install.RPiOsInstallCmd.run", side_effect=Exception("runner failure"))
    def test_cli_os_install_runner_failure(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "install",
            ],
        )

        self.assertEqual(1, run_call.call_count)
        self.assertIn("Failed to burn Raspbian OS", str(result.stdout))
        self.assertIsInstance(result.exception, CliApplicationException)
        self.assertEqual(str(result.exception), "runner failure")

    def test_integration_os_install_runner_darwin_cli_success(self) -> None:
        auto_prompt = "AUTO_PROMPT_RESPONSE"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=darwin_amd64",
                "os",
                "install",
            ],
        )
        cmd_output = str(result.stdout)
        self.assertIn("diskutil list", cmd_output)
        self.assertIn(f"diskutil unmountDisk {auto_prompt}", cmd_output)
        self.assertIn(f"unzip -p DRY_RUN_DOWNLOAD_FILE_PATH | sudo dd of={auto_prompt} bs=1m", cmd_output)
        self.assertIn("sync", cmd_output)
        self.assertIn(f"diskutil unmountDisk {auto_prompt}", cmd_output)
        self.assertIn(f"diskutil mountDisk {auto_prompt}", cmd_output)
        self.assertIn("sudo touch /Volumes/boot/ssh", cmd_output)
        self.assertIn(f"diskutil eject {auto_prompt}", cmd_output)

    def test_integration_os_install_runner_linux_cli_success(self) -> None:
        auto_prompt = "AUTO_PROMPT_RESPONSE"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=linux_amd64",
                "os",
                "install",
            ],
        )
        cmd_output = str(result.stdout)
        self.assertIn("lsblk -p", cmd_output)
        self.assertIn(
            f"unzip -p DRY_RUN_DOWNLOAD_FILE_PATH | dd of={auto_prompt} bs=4M conv=fsync status=progress", cmd_output
        )
        self.assertIn("sync", cmd_output)

    @mock.patch("rpi.os.configure.RPiOsConfigureRunner.run")
    def test_cli_os_configure_runner_with_cli_args_success(self, run_call: mock.MagicMock) -> None:
        expected_node_username = "test-user"
        expected_node_password = "test-user"
        expected_ip_discovery_range = "1.2.3.4"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "configure",
                f"--node-username={expected_node_username}",
                f"--node-password={expected_node_password}",
                f"--ip-discovery-range={expected_ip_discovery_range}",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_configure_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_configure_args)
        self.assertEqual(os_configure_args.node_username, expected_node_username)
        self.assertEqual(os_configure_args.node_password, expected_node_password)
        self.assertEqual(os_configure_args.ip_discovery_range, expected_ip_discovery_range)

    @mock.patch("rpi.os.configure.RPiOsConfigureRunner.run")
    def test_cli_os_configure_runner_with_config_args_success(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "configure"
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_configure_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_configure_args)
        self.assertEqual(os_configure_args.node_username, "pi")
        self.assertEqual(os_configure_args.node_password, "raspberry")
        self.assertEqual(os_configure_args.ip_discovery_range, "192.168.1.1/24")

    @mock.patch("rpi.os.configure.RPiOsConfigureRunner.run", side_effect=Exception("runner failure"))
    def test_cli_os_configure_runner_failure(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "configure",
            ],
        )

        self.assertEqual(1, run_call.call_count)
        self.assertIn("Failed to configure Raspbian OS", str(result.stdout))
        self.assertIsInstance(result.exception, CliApplicationException)
        self.assertEqual(str(result.exception), "runner failure")

    def test_integration_os_configure_runner_darwin_cli_success(self) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=darwin_amd64",
                "os",
                "configure",
            ],
        )
        working_dir = os.getcwd()
        cmd_output = str(result.stdout)
        self.assertIn(
            f"bash \
./external/shell_scripts_lib/runner/ansible/ansible.sh \
working_dir: {working_dir} \
username: AUTO_PROMPT_RESPONSE \
password: AUTO_PROMPT_RESPONSE \
playbook_path: rpi/os/playbooks/configure_os.yaml \
selected_host: AUTO_PROMPT_RESPONSE None \
ansible_var: host_name=AUTO_PROMPT_RESPONSE \
ansible_tag: configure_remote_node \
ansible_tag: reboot \
--dry-run",
            cmd_output,
        )

    def test_integration_os_configure_runner_linux_cli_success(self) -> None:
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--auto-prompt",
                "--os-arch=linux_amd64",
                "os",
                "configure",
            ],
        )
        working_dir = os.getcwd()
        cmd_output = str(result.stdout)
        self.assertIn(
            f"bash \
./external/shell_scripts_lib/runner/ansible/ansible.sh \
working_dir: {working_dir} \
username: AUTO_PROMPT_RESPONSE \
password: AUTO_PROMPT_RESPONSE \
playbook_path: rpi/os/playbooks/configure_os.yaml \
selected_host: AUTO_PROMPT_RESPONSE None \
ansible_var: host_name=AUTO_PROMPT_RESPONSE \
ansible_tag: configure_remote_node \
ansible_tag: reboot \
--dry-run",
            cmd_output,
        )

    @mock.patch("rpi.os.network.RPiNetworkConfigureRunner.run")
    def test_cli_os_network_runner_with_cli_args_success(self, run_call: mock.MagicMock) -> None:
        expected_static_ip_address = "1.1.1.1"
        expected_gw_ip_address = "1.2.3.4"
        expected_dns_ip_address = "4.3.2.1"
        expected_node_username = "test-user"
        expected_node_password = "test-user"
        expected_ip_discovery_range = "1.2.3.4"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "network",
                f"--static-ip-address={expected_static_ip_address}",
                f"--gw-ip-address={expected_gw_ip_address}",
                f"--dns-ip-address={expected_dns_ip_address}",
                f"--node-username={expected_node_username}",
                f"--node-password={expected_node_password}",
                f"--ip-discovery-range={expected_ip_discovery_range}",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_network_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_network_args)
        self.assertEqual(os_network_args.static_ip_address, expected_static_ip_address)
        self.assertEqual(os_network_args.gw_ip_address, expected_gw_ip_address)
        self.assertEqual(os_network_args.dns_ip_address, expected_dns_ip_address)
        self.assertEqual(os_network_args.node_username, expected_node_username)
        self.assertEqual(os_network_args.node_password, expected_node_password)
        self.assertEqual(os_network_args.ip_discovery_range, expected_ip_discovery_range)

    @mock.patch("rpi.os.network.RPiNetworkConfigureRunner.run")
    def test_cli_os_network_runner_with_config_args_success(self, run_call: mock.MagicMock) -> None:
        expected_static_ip_address = "1.1.1.1"
        result = runner.invoke(
            app,
            [
                "--dry-run",
                "--verbose",
                "os",
                "network",
                f"--static-ip-address={expected_static_ip_address}",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        os_configure_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(os_configure_args)
        self.assertEqual(os_configure_args.static_ip_address, expected_static_ip_address)
        self.assertEqual(os_configure_args.gw_ip_address, "192.168.1.1")
        self.assertEqual(os_configure_args.dns_ip_address, "192.168.1.1")
        self.assertEqual(os_configure_args.node_username, "pi")
        self.assertEqual(os_configure_args.node_password, "raspberry")
        self.assertEqual(os_configure_args.ip_discovery_range, "192.168.1.1/24")

    @mock.patch("rpi.os.network.RPiNetworkConfigureRunner.run", side_effect=Exception("runner failure"))
    def test_cli_os_network_runner_failure(self, run_call: mock.MagicMock) -> None:
        result = runner.invoke(
            app,
            ["--dry-run", "--verbose", "os", "network", "--static-ip-address=1.1.1.1"],
        )

        self.assertEqual(1, run_call.call_count)
        self.assertIn("Failed to configure RPi network", str(result.stdout))
        self.assertIsInstance(result.exception, CliApplicationException)
        self.assertEqual(str(result.exception), "runner failure")

    def test_integration_os_network_runner_darwin_cli_success(self) -> None:
        result = runner.invoke(
            app,
            ["--dry-run", "--auto-prompt", "--os-arch=darwin_amd64", "os", "network", "--static-ip-address=1.1.1.1"],
        )
        working_dir = os.getcwd()
        cmd_output = str(result.stdout)
        self.assertIn(
            f"bash \
./external/shell_scripts_lib/runner/ansible/ansible.sh \
working_dir: {working_dir} \
username: AUTO_PROMPT_RESPONSE \
password: AUTO_PROMPT_RESPONSE \
playbook_path: rpi/os/playbooks/configure_network.yaml \
selected_host: AUTO_PROMPT_RESPONSE None \
ansible_var: host_name=AUTO_PROMPT_RESPONSE \
ansible_var: static_ip=AUTO_PROMPT_RESPONSE \
ansible_var: gateway_address=AUTO_PROMPT_RESPONSE \
ansible_var: dns_address=AUTO_PROMPT_RESPONSE \
ansible_tag: configure_rpi_network \
ansible_tag: define_static_ip \
ansible_tag: reboot \
--dry-run",
            cmd_output,
        )

    def test_integration_os_network_runner_linux_cli_success(self) -> None:
        result = runner.invoke(
            app,
            ["--dry-run", "--auto-prompt", "--os-arch=darwin_amd64", "os", "network", "--static-ip-address=1.1.1.1"],
        )
        working_dir = os.getcwd()
        cmd_output = str(result.stdout)
        self.assertIn(
            f"bash \
./external/shell_scripts_lib/runner/ansible/ansible.sh \
working_dir: {working_dir} \
username: AUTO_PROMPT_RESPONSE \
password: AUTO_PROMPT_RESPONSE \
playbook_path: rpi/os/playbooks/configure_network.yaml \
selected_host: AUTO_PROMPT_RESPONSE None \
ansible_var: host_name=AUTO_PROMPT_RESPONSE \
ansible_var: static_ip=AUTO_PROMPT_RESPONSE \
ansible_var: gateway_address=AUTO_PROMPT_RESPONSE \
ansible_var: dns_address=AUTO_PROMPT_RESPONSE \
ansible_tag: configure_rpi_network \
ansible_tag: define_static_ip \
ansible_tag: reboot \
--dry-run",
            cmd_output,
        )
