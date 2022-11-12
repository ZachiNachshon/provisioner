#!/usr/bin/env python3

import unittest
from unittest import mock

# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os network
#
# To run as a single test target:
#  poetry run coverage run -m pytest rpi/os/network_test.py
#
# class RPiOsConfigureTestShould(unittest.TestCase):
#     def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
#         return FakeCollaborators(ctx)

#     def create_fake_config(self) -> ProvisionerConfig:
#         config = ProvisionerConfig(
#             {
#                 "provisioner": {
#                     "rpi": {
#                         "node": {
#                             "ip_discovery_range": "192.1.1.1/24",
#                             "username": "test-user",
#                             "password": "test-pass",
#                         },
#                         "ansible": {
#                             "playbooks": {
#                                 "configure_os": "/test/path/to/ansible/playbook",
#                             }
#                         },
#                     }
#                 }
#             }
#         )
#         return config

#     @mock.patch("common.remote.remote_os_configure.RemoteMachineNetworkConfigureRunner.run")
#     def test_configure_os_with_custom_config_successfully(self, run_call: mock.MagicMock) -> None:
#         ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

#         expected_username = "test-user"
#         expected_password = "test-pass"
#         expected_ip_discovery_range = "192.168.1.1/24"
#         expected_ansible_playbook_configure_os = "/test/path/to/ansible/playbook"

#         cols = self.create_fake_collaborators(ctx)
#         fake_config = self.create_fake_config()
#         cols.config_reader.register_internal_path_config(path=CONFIG_INTERNAL_PATH, class_obj=fake_config)

#         args = RPiOsConfigureArgs(
#             node_username=expected_username,
#             node_password=expected_password,
#             ip_discovery_range=expected_ip_discovery_range,
#         )

#         runner = RPiOsConfigureRunner()
#         runner.run(ctx=ctx, args=args, collaborators=cols)

#         run_call_kwargs = run_call.call_args.kwargs
#         ctx_call_arg = run_call_kwargs["ctx"]
#         img_burner_call_args = run_call_kwargs["args"]

#         self.assertEqual(ctx, ctx_call_arg)
#         self.assertEqual(expected_username, img_burner_call_args.node_username)
#         self.assertEqual(expected_password, img_burner_call_args.node_password)
#         self.assertEqual(expected_ip_discovery_range, img_burner_call_args.ip_discovery_range)
#         self.assertEqual(
#             expected_ansible_playbook_configure_os, img_burner_call_args.ansible_playbook_path_configure_os
#         )

#     @mock.patch("common.remote.remote_os_configure.RemoteMachineNetworkConfigureRunner.run")
#     def test_configure_os_with_default_config_successfully(self, run_call: mock.MagicMock) -> None:
#         ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

#         cols = self.create_fake_collaborators(ctx)
#         fake_config = self.create_fake_config()
#         cols.config_reader.register_internal_path_config(path=CONFIG_INTERNAL_PATH, class_obj=fake_config)

#         args = RPiOsConfigureArgs()
#         runner = RPiOsConfigureRunner()
#         runner.run(ctx=ctx, args=args, collaborators=cols)

#         run_call_kwargs = run_call.call_args.kwargs
#         ctx_call_arg = run_call_kwargs["ctx"]
#         img_burner_call_args = run_call_kwargs["args"]

#         self.assertEqual(ctx, ctx_call_arg)
#         self.assertEqual(fake_config.node_username, img_burner_call_args.node_username)
#         self.assertEqual(fake_config.node_password, img_burner_call_args.node_password)
#         self.assertEqual(fake_config.ip_discovery_range, img_burner_call_args.ip_discovery_range)
#         self.assertEqual(
#             fake_config.ansible_playbook_path_configure_os, img_burner_call_args.ansible_playbook_path_configure_os
#         )
