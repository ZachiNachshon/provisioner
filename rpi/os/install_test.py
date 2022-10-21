#!/usr/bin/env python3

import unittest
from unittest import mock

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.os import MAC_OS, OsArch
from rpi.os.install import RPiOsInstallCmd, RPiOsInstallCmdArgs


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run os install
#
class RPiOsInstallTestShould(unittest.TestCase):
    @mock.patch("common.sd_card.image_burner.ImageBurnerCmdRunner.run")
    def test_burn_os_raspbian_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        download_url = "https://burn-image-test-custom.com"
        download_path = "/test/download/path"

        args = RPiOsInstallCmdArgs(image_download_url=download_url, image_download_path=download_path)
        runner = RPiOsInstallCmd()
        runner.run(ctx=ctx, args=args)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        img_burner_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(download_url, img_burner_call_args.image_download_url)
        self.assertEqual(download_path, img_burner_call_args.image_download_path)
