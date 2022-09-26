#!/usr/bin/env python3

import unittest

from rpi.os.domain.config import ProvisionerConfig
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import FailedToSerializeConfiguration, NotInitialized
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

class ProvisionerConfigTestShould(unittest.TestCase):

    def test_config_partial_merge_with_user_config(self):
        yaml_util = YamlUtil.create(IOUtils.create(Context.create()))
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
        yaml_util = YamlUtil.create(IOUtils.create(Context.create()))
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
        64bit:
          download_url: http://download-url-64-bit-user.com
        32bit:
          download_url: http://download-url-32-bit-user.com

"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)
        merged_config_obj = internal_config_obj.merge(user_config_obj)

        self.assertEqual(merged_config_obj.active_system, "32bit")
        self.assertEqual(merged_config_obj.download_url_32bit, "http://download-url-32-bit-user.com")
        self.assertEqual(merged_config_obj.download_url_64bit, "http://download-url-64-bit-user.com")


    def test_config_fail_on_invalid_user_config(self):
        yaml_util = YamlUtil.create(IOUtils.create(Context.create()))
        user_yaml_str = """
provisioner:
  rpi:
    os:
    active_system: 32bit
"""
        with self.assertRaises(FailedToSerializeConfiguration):
            yaml_util.read_string_fn(yaml_str=user_yaml_str, class_name=ProvisionerConfig)

    def test_read_os_raspi_download_url(self):
        yaml_util = YamlUtil.create(IOUtils.create(Context.create()))
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