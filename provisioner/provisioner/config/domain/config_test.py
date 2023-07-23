#!/usr/bin/env python3

import os
import unittest

from python_core_lib.errors.cli_errors import FailedToSerializeConfiguration
from python_core_lib.infra.context import Context
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.yaml_util import YamlUtil

from provisioner.config.domain.config import ProvisionerConfig


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner/config/domain/config_test.py
#
class ProvisionerConfigTestShould(unittest.TestCase):
    def test_config_partial_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
provisioner:
  remote:
    hosts:
      - name: test-node
        address: 1.1.1.1
        auth:
          username: pi
          password: raspberry
          ssh_private_key_file_path: /path/to/unknown

    lan_scan:
      ip_discovery_range: 192.168.1.1/24

  single_board:
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
  remote:
    hosts:
      - name: test-node
        address: 1.1.1.1
        auth:
          username: test-user
          ssh_private_key_file_path: /test/path

  single_board:
    os:
      raspbian:
        active_system: 32bit
        download_url:
          32bit: http://download-url-32-bit-test-path.com
"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)
        merged_config_obj = internal_config_obj.merge(user_config_obj)

        self.assertEqual(len(merged_config_obj.remote.hosts), 1)
        self.assertEqual(merged_config_obj.remote.hosts["test-node"].name, "test-node")
        self.assertEqual(merged_config_obj.remote.hosts["test-node"].address, "1.1.1.1")
        self.assertEqual(merged_config_obj.remote.hosts["test-node"].auth.username, "test-user")
        self.assertIsNone(merged_config_obj.remote.hosts["test-node"].auth.password)
        self.assertEqual(merged_config_obj.remote.hosts["test-node"].auth.ssh_private_key_file_path, "/test/path")

        self.assertEqual(merged_config_obj.remote.lan_scan.ip_discovery_range, "192.168.1.1/24")

        self.assertEqual(merged_config_obj.single_board.os.active_system, "32bit")
        self.assertEqual(
            merged_config_obj.single_board.os.download_url_32bit, "http://download-url-32-bit-test-path.com"
        )
        self.assertEqual(merged_config_obj.single_board.os.download_url_64bit, "http://download-url-64-bit.com")

    def test_config_full_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
provisioner:
  remote:
    hosts:
      - name: kmaster
        address: 192.168.1.200
        auth:
          username: pi
          password: raspberry
          ssh_private_key_file_path: /path/to/unknown

      - name: knode1
        address: 192.168.1.201
        auth:
          username: pi
          password: raspberry
          ssh_private_key_file_path: /path/to/unknown

    lan_scan:
      ip_discovery_range: 192.168.1.1/24

  single_board:
    os:
      raspbian:
        active_system: 64bit
        download_path: $HOME/temp/rpi_raspios_image
        download_url:
          64bit: http://download-url-64-bit.com
          32bit: http://download-url-32-bit.com

    network:
      gw_ip_address: 192.168.1.1
      dns_ip_address: 192.168.1.1

  anchor:
    github:
      organization: ZachiNachshon
      repository: provisioner
      branch: master
      git_access_token: SECRET

  dummy:
    hello_world:
      username: Config User
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)

        user_yaml_str = """
provisioner:
  remote:
    hosts:
      - name: kmaster-new
        address: 192.168.1.300
        auth:
          username: pi-user
          password: raspberry-user
          ssh_private_key_file_path: /path/to/unknown/test-user

      - name: knode1-new
        address: 192.168.1.301
        auth:
          username: pi-user
          password: raspberry-user
          ssh_private_key_file_path: /path/to/unknown/test-user

    lan_scan:
      ip_discovery_range: 1.1.1.1/24

  anchor:
    github:
      organization: TestOrg
      repository: test-repo
      branch: test
      git_access_token: TEST-SECRET

  dummy:
    hello_world:
      username: Config Test User

  single_board:
    os:
      raspbian:
        active_system: 32bit
        download_path: $HOME/temp/rpi_raspios_image_user
        download_url:
          64bit: http://download-url-64-bit-user.com
          32bit: http://download-url-32-bit-user.com

    network:
      gw_ip_address: 1.1.1.1
      dns_ip_address: 2.2.2.2
"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)
        merged_config_obj = internal_config_obj.merge(user_config_obj)

        self.assertEqual(len(merged_config_obj.remote.hosts), 2)
        self.assertEqual(merged_config_obj.remote.hosts["kmaster-new"].name, "kmaster-new")
        self.assertEqual(merged_config_obj.remote.hosts["kmaster-new"].address, "192.168.1.300")
        self.assertEqual(merged_config_obj.remote.hosts["kmaster-new"].auth.username, "pi-user")
        self.assertEqual(merged_config_obj.remote.hosts["kmaster-new"].auth.password, "raspberry-user")
        self.assertEqual(
            merged_config_obj.remote.hosts["kmaster-new"].auth.ssh_private_key_file_path, "/path/to/unknown/test-user"
        )

        self.assertEqual(merged_config_obj.remote.hosts["knode1-new"].name, "knode1-new")
        self.assertEqual(merged_config_obj.remote.hosts["knode1-new"].address, "192.168.1.301")
        self.assertEqual(merged_config_obj.remote.hosts["knode1-new"].auth.username, "pi-user")
        self.assertEqual(merged_config_obj.remote.hosts["knode1-new"].auth.password, "raspberry-user")
        self.assertEqual(
            merged_config_obj.remote.hosts["knode1-new"].auth.ssh_private_key_file_path, "/path/to/unknown/test-user"
        )

        self.assertEqual(merged_config_obj.remote.lan_scan.ip_discovery_range, "1.1.1.1/24")

        self.assertEqual(merged_config_obj.anchor.github.organization, "TestOrg")
        self.assertEqual(merged_config_obj.anchor.github.repository, "test-repo")
        self.assertEqual(merged_config_obj.anchor.github.branch, "test")
        self.assertEqual(merged_config_obj.anchor.github.git_access_token, "TEST-SECRET")

        self.assertEqual(merged_config_obj.dummmy.hello_world.username, "Config Test User")

        self.assertEqual(merged_config_obj.single_board.os.active_system, "32bit")
        self.assertEqual(
            merged_config_obj.single_board.os.download_path, os.path.expanduser("~/temp/rpi_raspios_image_user")
        )
        self.assertEqual(merged_config_obj.single_board.os.download_url_32bit, "http://download-url-32-bit-user.com")
        self.assertEqual(merged_config_obj.single_board.os.download_url_64bit, "http://download-url-64-bit-user.com")

        self.assertEqual(merged_config_obj.single_board.network.gw_ip_address, "1.1.1.1")
        self.assertEqual(merged_config_obj.single_board.network.dns_ip_address, "2.2.2.2")

    def test_config_fail_on_invalid_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        user_yaml_str = """
provisioner:
  single_board:
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
  single_board:
    os:
      raspbian:
        active_system: 32bit
        download_url:
          64bit: http://download-url-64-bit.com
          32bit: http://download-url-32-bit.com
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)
        internal_config_obj.single_board.get_os_raspbian_download_url()
        self.assertEqual(internal_config_obj.single_board.os.download_url_32bit, "http://download-url-32-bit.com")
