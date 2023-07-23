#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.checks_fakes import FakeChecks
from python_core_lib.utils.os import LINUX, MAC_OS, WINDOWS, OsArch

from provisioner_features_lib.sd_card.image_burner import (
    ImageBurnerArgs,
    ImageBurnerCmdRunner,
)

#
# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/sd_card/image_burner_test.py
#
ARG_IMAGE_DOWNLOAD_URL = "https://burn-image-test.com"
ARG_IMAGE_DOWNLOAD_PATH = "/path/to/downloaded/image"

SELECTED_BLOCK_DEVICE = "/dev/diskT"
SELECTED_BLOCK_DEVICE_DARWIN = "/dev/rdiskT"
BLOCK_DEVICES_OUTPUT = """
/dev/disk0 (internal, physical):
   #:                       TYPE NAME                    SIZE       IDENTIFIER
   0:      GUID_partition_scheme                        *1.0 TB     diskA
   1:             Apple_APFS_ISC Container diskX         524.3 MB   diskAsX
   2:                 Apple_APFS Container diskY         994.7 GB   diskAsY
   3:        Apple_APFS_Recovery Container diskZ         5.4 GB     diskAsZ
   4:             Test_Disk_Type Container diskT         32.0 GB    /dev/diskT

/dev/disk3 (synthesized):
   #:                       TYPE NAME                    SIZE       IDENTIFIER
   0:      APFS Container Scheme -                      +994.7 GB   diskZ
                                 Physical Store disk0s2
   1:                APFS Volume Macintosh HD            8.9 GB     diskBsA
   2:              APFS Snapshot com.apple.os.update-... 8.9 GB     diskBsAsA
   3:                APFS Volume Preboot                 4.8 GB     diskBsB
   4:                APFS Volume Recovery                906.8 MB   diskBsC
   5:                APFS Volume Macintosh HD - Data     196.3 GB   diskBsE
   6:                APFS Volume VM                      3.2 GB     diskBsF
"""

SD_CARD_IMAGE_BURNER_RUNNER_PATH = "provisioner_features_lib.sd_card.image_burner.ImageBurnerCmdRunner"


class ImageBurnerTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_image_burner_args(self) -> ImageBurnerArgs:
        return ImageBurnerArgs(image_download_url=ARG_IMAGE_DOWNLOAD_URL, image_download_path=ARG_IMAGE_DOWNLOAD_PATH)

    def test_prerequisites_darwin_success(self) -> None:
        fake_checks = FakeChecks.create(self.env.get_context())
        fake_checks.mock_utility("diskutil")
        fake_checks.mock_utility("unzip")
        fake_checks.mock_utility("dd")

        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS)),
                fake_checks,
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        fake_checks = FakeChecks.create(self.env.get_context())
        fake_checks.mock_utility("lsblk")
        fake_checks.mock_utility("unzip")
        fake_checks.mock_utility("dd")
        fake_checks.mock_utility("sync")

        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX)),
                fake_checks,
            ),
        )

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=WINDOWS)), None
            ),
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os="NOT-SUPPORTED")), None
            ),
        )

    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._print_pre_run_instructions(env.get_collaborators())
        Assertion.expect_success(
            self, method_to_run=lambda: env.get_collaborators().prompter().assert_enter_prompt_count(1)
        )

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._prerequisites")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._print_pre_run_instructions")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._select_block_device")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._download_image")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._burn_image_by_os")
    def test_main_flow_run_actions_have_expected_order(
        self,
        burn_image_by_os_call: mock.MagicMock,
        download_image_call: mock.MagicMock,
        select_block_device_call: mock.MagicMock,
        pre_run_call: mock.MagicMock,
        prerequisites_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner().run(env.get_context(), self.create_fake_image_burner_args(), env.get_collaborators())
        prerequisites_call.assert_called_once()
        pre_run_call.assert_called_once()
        select_block_device_call.assert_called_once()
        download_image_call.assert_called_once()
        burn_image_by_os_call.assert_called_once()

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._ask_user_to_select_block_devices")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._print_and_return_block_devices_output")
    def test_select_block_device_with_expected_prompt(
        self, print_block_devices_call: mock.MagicMock, ask_user_for_block_devices_call: mock.MagicMock
    ) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._select_block_device(env.get_context(), env.get_collaborators())
        env.get_collaborators().printer().assert_output("Block device selection:")

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._read_block_devices", return_value=BLOCK_DEVICES_OUTPUT)
    def test_print_and_return_block_devices_output(self, read_block_devices_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._print_and_return_block_devices_output(env.get_context(), env.get_collaborators())
        env.get_collaborators().printer().assert_output(BLOCK_DEVICES_OUTPUT)

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._verify_block_device_name")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._prompt_for_block_device_name", return_value=SELECTED_BLOCK_DEVICE)
    def test_ask_user_to_select_block_devices(
        self, prompt_for_block_device_name_call: mock.MagicMock, verify_block_device_name_call: mock.MagicMock
    ) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._ask_user_to_select_block_devices(
            env.get_context(), env.get_collaborators(), BLOCK_DEVICES_OUTPUT
        )
        env.get_collaborators().summary().assert_value("block_device_name", SELECTED_BLOCK_DEVICE)

    def test_verify_block_device_name_valid(self) -> None:
        self.assertTrue(ImageBurnerCmdRunner()._verify_block_device_name(BLOCK_DEVICES_OUTPUT, SELECTED_BLOCK_DEVICE))

    def test_verify_block_device_name_invalid(self) -> None:
        self.assertFalse(ImageBurnerCmdRunner()._verify_block_device_name(BLOCK_DEVICES_OUTPUT, "invalid"))

    def test_prompt_for_block_device_name(self) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._prompt_for_block_device_name(env.get_collaborators())
        env.get_collaborators().printer().assert_output("Please select a block device:")
        env.get_collaborators().prompter().assert_user_input_prompt("Type block device name")

    def test_download_image(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().http_client().mock_download_file_response(
            ARG_IMAGE_DOWNLOAD_URL, ARG_IMAGE_DOWNLOAD_PATH
        )
        ImageBurnerCmdRunner()._download_image(
            env.get_context(), ARG_IMAGE_DOWNLOAD_URL, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators()
        )
        env.get_collaborators().http_client().assert_download_file(ARG_IMAGE_DOWNLOAD_URL)
        env.get_collaborators().summary().assert_value("image_file_path", ARG_IMAGE_DOWNLOAD_PATH)

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._burn_image_linux")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._run_pre_burn_approval_flow")
    def test_burn_image_by_os_linux(
        self, run_pre_burn_approval_flow_call: mock.MagicMock, burn_image_linux_call: mock.MagicMock
    ) -> None:
        env = TestEnv.create(ctx=Context.create(os_arch=OsArch(os=LINUX)))
        ImageBurnerCmdRunner()._burn_image_by_os(
            env.get_context(), SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators()
        )
        run_pre_burn_approval_flow_call.assert_called_once()
        burn_image_linux_call.assert_called_once()

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._burn_image_darwin")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._run_pre_burn_approval_flow")
    def test_burn_image_by_os_darwin(
        self, run_pre_burn_approval_flow_call: mock.MagicMock, burn_image_darwin_call: mock.MagicMock
    ) -> None:
        env = TestEnv.create(ctx=Context.create(os_arch=OsArch(os=MAC_OS)))
        ImageBurnerCmdRunner()._burn_image_by_os(
            env.get_context(), SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators()
        )
        run_pre_burn_approval_flow_call.assert_called_once()
        burn_image_darwin_call.assert_called_once()

    def test_burn_image_fail_on_os_not_supported(self) -> None:
        env = TestEnv.create()
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._burn_image_by_os(
                Context.create(os_arch=OsArch(os=WINDOWS)),
                SELECTED_BLOCK_DEVICE,
                ARG_IMAGE_DOWNLOAD_PATH,
                env.get_collaborators(),
            ),
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._burn_image_by_os(
                Context.create(os_arch=OsArch(os="NOT-SUPPORTED")),
                SELECTED_BLOCK_DEVICE,
                ARG_IMAGE_DOWNLOAD_PATH,
                env.get_collaborators(),
            ),
        )

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._ask_to_verify_block_device")
    def test_run_pre_burn_approval_flow(self, ask_to_verify_block_device_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._run_pre_burn_approval_flow(
            env.get_context(), SELECTED_BLOCK_DEVICE, env.get_collaborators()
        )
        env.get_collaborators().summary().assert_show_summay_title(f"Burning image to {SELECTED_BLOCK_DEVICE}")
        ask_to_verify_block_device_call.assert_called_once()

    def test_burn_image_linux(self) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._burn_image_linux(
            SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators()
        )
        env.get_collaborators().printer().assert_outputs(
            [
                "Formatting block device and burning a new image...",
                "Flushing write-cache...",
                "It is now safe to remove the SD-Card !",
            ]
        )
        env.get_collaborators().process().assert_run_commands(
            [
                [
                    f"unzip -p {ARG_IMAGE_DOWNLOAD_PATH} | dd of={SELECTED_BLOCK_DEVICE} bs=4M conv=fsync status=progress"
                ],
                ["sync"],
            ]
        )

    def test_burn_image_darwin(self) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._burn_image_darwin(
            SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators()
        )
        env.get_collaborators().printer().assert_outputs(
            [
                "Unmounting selected block device (SD-Card)...",
                "Formatting block device and burning a new image (Press Ctrl+T to show progress)...",
                "Flushing write-cache to block device...",
                f"Remounting block device {SELECTED_BLOCK_DEVICE}...",
                "Allowing SSH access...",
                f"Ejecting block device {SELECTED_BLOCK_DEVICE}...",
                "It is now safe to remove the SD-Card !",
            ]
        )
        env.get_collaborators().process().assert_run_commands(
            [
                ["diskutil", "unmountDisk", SELECTED_BLOCK_DEVICE],
                [f"unzip -p {ARG_IMAGE_DOWNLOAD_PATH} | sudo dd of={SELECTED_BLOCK_DEVICE_DARWIN} bs=1m"],
                ["sync"],
                ["diskutil", "unmountDisk", SELECTED_BLOCK_DEVICE],
                ["diskutil", "mountDisk", SELECTED_BLOCK_DEVICE],
                ["sudo", "touch", "/Volumes/boot/ssh"],
                ["diskutil", "eject", SELECTED_BLOCK_DEVICE],
            ]
        )

    def test_read_block_devices_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os=MAC_OS)),
                self.env.get_collaborators(),
            ),
        )
        self.env.get_collaborators().process().assert_run_command(args=["diskutil", "list"])

    def test_read_block_devices_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os=LINUX)),
                self.env.get_collaborators(),
            ),
        )
        self.env.get_collaborators().process().assert_run_command(args=["lsblk", "-p"])

    def test_read_block_devices_fail_on_os_not_supported(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os=WINDOWS)), None
            ),
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os="NOT-SUPPORTED")), None
            ),
        )

    def test_ask_to_verify_block_device(self) -> None:
        env = TestEnv.create()
        ImageBurnerCmdRunner()._ask_to_verify_block_device(SELECTED_BLOCK_DEVICE, env.get_collaborators())
        env.get_collaborators().prompter().assert_yes_no_prompt(
            f"ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE '{SELECTED_BLOCK_DEVICE}'"
        )
