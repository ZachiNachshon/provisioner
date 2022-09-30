#!/usr/bin/env python3

import os
import unittest

from rpi.os.domain.config import ProvisionerConfig
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import FailedToSerializeConfiguration, NotInitialized
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

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
        64bit:
          download_url: http://download-url-64-bit.com
        32bit:
          download_url: http://download-url-32-bit.com
"""        
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)

        user_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 32bit
        32bit:
          download_url: http://download-url-32-bit-user.com

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
        64bit:
          download_url: http://download-url-64-bit.com
        32bit:
          download_url: http://download-url-32-bit.com

    node:
      ip_discovery_range: 192.168.1.100/24
      username: pi
      password: raspberry

    ansible:
      playbook:
        path: external/ansible_playbooks/playbooks/roles/rpi_config_node
"""        
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)

        user_yaml_str = """
provisioner:
  rpi:
    os:
      raspbian:
        active_system: 32bit
        download_path: $HOME/temp/rpi_raspios_image_user
        64bit:
          download_url: http://download-url-64-bit-user.com
        32bit:
          download_url: http://download-url-32-bit-user.com

    node:
      ip_discovery_range: 1.1.1.1/24
      username: pi-user
      password: raspberry-user

    ansible:
      playbook:
        path: external/ansible_playbooks/playbooks/roles/rpi_config_node-user

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
        self.assertEqual(merged_config_obj.ansible_playbook_folder_path, "external/ansible_playbooks/playbooks/roles/rpi_config_node-user")


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
        64bit:
          download_url: http://download-url-64-bit.com
        32bit:
          download_url: http://download-url-32-bit.com
"""        
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, class_name=ProvisionerConfig)
        internal_config_obj.get_os_raspbian_download_url()
        self.assertEqual(internal_config_obj.download_url_32bit, "http://download-url-32-bit.com")