#!/usr/bin/env python3

import unittest
from unittest import mock

from external.python_scripts_lib.infra.context import Context
from rpi.os.install import RPiOsInstallArgs, RPiOsInstallRunner, Collaborators
from external.python_scripts_lib.utils.os import MAC_OS, OsArch
from external.python_scripts_lib.utils.io_utils_fakes import FakeIOUtils
from external.python_scripts_lib.utils.properties_fakes import FakeProperties


class FakeCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        print("Creating Fake collaborators...")
        self.io = FakeIOUtils.create()
        self.properties = FakeProperties.create(ctx, io_utils=self.io)


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run os install
#
class RPiOsInstallTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.run")
    def test_burn_os_raspbian_with_custom_url_successfully(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        download_url = "https://burn-image-test.com"

        cols = self.create_fake_collaborators(ctx)
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

        download_url = "https://burn-image-test.com"

        cols = self.create_fake_collaborators(ctx)
        cols.properties.register_property_key("rpi.os.raspbian.os.system", "128")
        cols.properties.register_property_key("rpi.os.raspbian.128.bit.download.url", download_url)

        args = RPiOsInstallArgs()
        runner = RPiOsInstallRunner()
        runner.run(ctx=ctx, args=args, collaborators=cols)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        img_burner_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(download_url, img_burner_call_args.image_download_url)
