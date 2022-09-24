#!/usr/bin/env python3

import unittest
from unittest import mock

from rpi.os.install import RPiOsInstallArgs, RPiOsInstallRunner, Collaborators
from rpi.os.domain.config import ProvisionerConfig
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.os import MAC_OS, OsArch
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from external.python_scripts_lib.python_scripts_lib.utils.io_utils_fakes import FakeIOUtils
from external.python_scripts_lib.python_scripts_lib.config.config_reader_fakes import FakeConfigReader

CONFIG_INTERNAL_PATH = "rpi/config.yaml"

class FakeCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        print("Creating Fake collaborators...")
        self.io = FakeIOUtils.create(ctx)
        self.config_reader = FakeConfigReader.create(yaml_util=YamlUtil.create(self.io))

#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run os install
#
class RPiOsInstallTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def create_fake_config(self) -> ProvisionerConfig:
        config = ProvisionerConfig({
            "provisioner": {
                "rpi": {
                    "os": {
                        "raspbian": {
                            "activeSystem": "64bit",
                            "32bit": {
                                "downloadUrl": "https://burn-image-test-32-bit.com"
                            },
                            "64bit": {
                                "downloadUrl": "https://burn-image-test-64-bit.com"
                            }
                        }
                    }
                }
            }
        })
        return config 

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.run")
    def test_burn_os_raspbian_with_custom_url_successfully(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        download_url = "https://burn-image-test-custom.com"

        cols = self.create_fake_collaborators(ctx)
        fake_config = self.create_fake_config()
        cols.config_reader.register_internal_path_config(path=CONFIG_INTERNAL_PATH, class_obj=fake_config)

        args = RPiOsInstallArgs(image_download_url=download_url)
        runner = RPiOsInstallRunner()
        runner.run(ctx=ctx, args=args, collaborators=cols)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        img_burner_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(download_url, img_burner_call_args.image_download_url)

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.run")
    def test_burn_os_raspbian_with_default_url_successfully(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        fake_config = self.create_fake_config()
        cols.config_reader.register_internal_path_config(path=CONFIG_INTERNAL_PATH, class_obj=fake_config)

        args = RPiOsInstallArgs()
        runner = RPiOsInstallRunner()
        runner.run(ctx=ctx, args=args, collaborators=cols)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        img_burner_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(fake_config.download_url_64bit, img_burner_call_args.image_download_url)
