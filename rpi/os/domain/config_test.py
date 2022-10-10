#!/usr/bin/env python3

import os
import unittest

from rpi.os.domain.config import ProvisionerConfig
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    FailedToSerializeConfiguration,
    NotInitialized,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil


# To run as a single test target:
# poetry run coverage run -m pytest rpi/os/domain/config_test.py
# 
class ProvisionerConfigTestShould(unittest.TestCase):
    def test_config_partial_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 64bit
        download_url:
          64bit: http://download-url-64-bit.com
          32bit: http://download-url-32-bit.com
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)

        user_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 32bit
        download_url:
          32bit: http://download-url-32-bit-user.com
"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)
        merged_config_obj = internal_config_obj.merge(user_config_obj)

        self.assertEqual(merged_config_obj.active_system, "32bit")
        self.assertEqual(merged_config_obj.download_url_32bit, "http://download-url-32-bit-user.com")

    def test_config_full_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 64bit
        download_path: $HOME/temp/rpi_raspios_image
        download_url:
          64bit: http://download-url-64-bit.com
          32bit: http://download-url-32-bit.com

    node:
      ip_discovery_range: 192.168.1.1/24
      username: pi
      password: raspberry
      gw_ip_address: 192.168.1.1
      dns_ip_address: 192.168.1.1

    ansible:
      playbooks:
        configure_os: rpi/os/playbooks/configure_os.yaml
        configure_network: rpi/os/playbooks/configure_network.yaml
        wait_for_network: rpi/os/playbooks/wait_for_network.yaml
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)

        user_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 32bit
        download_path: $HOME/temp/rpi_raspios_image_user
        download_url:
          64bit: http://download-url-64-bit-user.com
          32bit: http://download-url-32-bit-user.com

    node:
      ip_discovery_range: 1.1.1.1/24
      username: pi-user
      password: raspberry-user
      gw_ip_address: 1.1.1.1
      dns_ip_address: 2.2.2.2

    ansible:
      playbooks:
        configure_os: rpi/os/playbooks/configure_os_user.yaml
        configure_network: rpi/os/playbooks/configure_network_user.yaml
        wait_for_network: rpi/os/playbooks/wait_for_network_user.yaml
"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)
        merged_config_obj = internal_config_obj.merge(user_config_obj)

        self.assertEqual(merged_config_obj.active_system, "32bit")
        self.assertEqual(merged_config_obj.download_path, os.path.expanduser("~/temp/rpi_raspios_image_user"))
        self.assertEqual(merged_config_obj.download_url_32bit, "http://download-url-32-bit-user.com")
        self.assertEqual(merged_config_obj.download_url_64bit, "http://download-url-64-bit-user.com")
        self.assertEqual(merged_config_obj.ip_discovery_range, "1.1.1.1/24")
        self.assertEqual(merged_config_obj.node_username, "pi-user")
        self.assertEqual(merged_config_obj.node_password, "raspberry-user")
        self.assertEqual(merged_config_obj.gw_ip_address, "1.1.1.1")
        self.assertEqual(merged_config_obj.dns_ip_address, "2.2.2.2")
        self.assertEqual(
            merged_config_obj.ansible_playbook_path_configure_os,
            "rpi/os/playbooks/configure_os_user.yaml",
        )
        self.assertEqual(
            merged_config_obj.ansible_playbook_path_configure_network,
            "rpi/os/playbooks/configure_network_user.yaml",
        )
        self.assertEqual(
            merged_config_obj.ansible_playbook_path_wait_for_network,
            "rpi/os/playbooks/wait_for_network_user.yaml",
        )

    def test_config_fail_on_invalid_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        user_yaml_str = """
provisioner:
  rpi:
    os:
    active_system: 32bit
"""
        with self.assertRaises(FailedToSerializeConfiguration):
            yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)

    def test_read_os_raspi_download_url(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 32bit
        download_url:
          64bit: http://download-url-64-bit.com
          32bit: http://download-url-32-bit.com
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)
        internal_config_obj.get_os_raspbian_download_url()
        self.assertEqual(internal_config_obj.download_url_32bit, "http://download-url-32-bit.com")
