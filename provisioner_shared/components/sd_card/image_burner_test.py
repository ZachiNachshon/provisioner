#!/usr/bin/env python3

import unittest
from typing import List
from unittest import mock

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.checks_fakes import FakeChecks
from provisioner_shared.components.runtime.utils.os import LINUX, MAC_OS, WINDOWS, OsArch
from provisioner_shared.components.runtime.utils.prompter import PromptLevel
from provisioner_shared.components.sd_card.image_burner import (
    ImageBurnerArgs,
    ImageBurnerCmdRunner,
)
from provisioner_shared.test_lib import faker
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

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

SD_CARD_IMAGE_BURNER_RUNNER_PATH = "provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner"


class ImageBurnerTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_image_burner_args(self) -> ImageBurnerArgs:
        return ImageBurnerArgs(
            image_download_url=ARG_IMAGE_DOWNLOAD_URL,
            image_download_path=ARG_IMAGE_DOWNLOAD_PATH,
        )

    def test_prerequisites_darwin_success(self) -> None:
        fake_checks = FakeChecks.create(self.env.get_context())
        expected_tools = ["diskutil", "dd"]
        call_count = 0
        
        def check_tool_side_effect(tool):
            nonlocal call_count
            self.assertIn(tool, expected_tools)
            call_count += 1
            return True  # Return success
            
        fake_checks.on("check_tool_fn", str).side_effect = check_tool_side_effect

        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS)),
                fake_checks,
            ),
        )
        self.assertEqual(call_count, len(expected_tools))

    def test_prerequisites_linux_success(self) -> None:
        fake_checks = FakeChecks.create(self.env.get_context())
        expected_tools = ["lsblk", "dd", "sync"]
        call_count = 0
        
        def check_tool_side_effect(tool):
            nonlocal call_count
            self.assertIn(tool, expected_tools)
            call_count += 1
            return True  # Return success
            
        fake_checks.on("check_tool_fn", str).side_effect = check_tool_side_effect

        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX)),
                fake_checks,
            ),
        )
        self.assertEqual(call_count, len(expected_tools))

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
        env.get_collaborators().printer().on("print_fn", str).side_effect = None
        env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = None
        env.get_collaborators().prompter().on("prompt_for_enter_fn", PromptLevel).side_effect = None
        ImageBurnerCmdRunner()._print_pre_run_instructions(env.get_collaborators())

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
        ImageBurnerCmdRunner().run(
            env.get_context(),
            self.create_fake_image_burner_args(),
            env.get_collaborators(),
        )
        prerequisites_call.assert_called_once()
        pre_run_call.assert_called_once()
        select_block_device_call.assert_called_once()
        download_image_call.assert_called_once()
        burn_image_by_os_call.assert_called_once()

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._ask_user_to_select_block_devices")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._print_and_return_block_devices_output")
    def test_select_block_device_with_expected_prompt(
        self,
        print_block_devices_call: mock.MagicMock,
        ask_user_for_block_devices_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, "Block device selection:"
        )
        env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        ImageBurnerCmdRunner()._select_block_device(env.get_context(), env.get_collaborators())

    @mock.patch(
        f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._read_block_devices",
        return_value=BLOCK_DEVICES_OUTPUT,
    )
    def test_print_and_return_block_devices_output(self, read_block_devices_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, BLOCK_DEVICES_OUTPUT
        )
        ImageBurnerCmdRunner()._print_and_return_block_devices_output(env.get_context(), env.get_collaborators())

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._verify_block_device_name")
    @mock.patch(
        f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._prompt_for_block_device_name",
        return_value=SELECTED_BLOCK_DEVICE,
    )
    def test_ask_user_to_select_block_devices(
        self,
        prompt_for_block_device_name_call: mock.MagicMock,
        verify_block_device_name_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        env.get_collaborators().summary().on("append", str, str).side_effect = lambda attribute_name, value: (
            self.assertEqual(attribute_name, "block_device_name"),
            self.assertEqual(value, SELECTED_BLOCK_DEVICE),
        )
        ImageBurnerCmdRunner()._ask_user_to_select_block_devices(
            env.get_context(), env.get_collaborators(), BLOCK_DEVICES_OUTPUT
        )

    def test_verify_block_device_name_valid(self) -> None:
        self.assertTrue(ImageBurnerCmdRunner()._verify_block_device_name(BLOCK_DEVICES_OUTPUT, SELECTED_BLOCK_DEVICE))

    def test_verify_block_device_name_invalid(self) -> None:
        self.assertFalse(ImageBurnerCmdRunner()._verify_block_device_name(BLOCK_DEVICES_OUTPUT, "invalid"))

    def test_prompt_for_block_device_name(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, "Please select a block device:"
        )
        env.get_collaborators().printer().on("new_line_fn", int).side_effect = None

        def prompt_assertion_callback(
            message: str,
            default: str,
            is_password: bool,
            level: PromptLevel,
            post_user_input_message: str,
        ) -> None:
            self.assertEqual(message, "Please type the block device name")
            self.assertEqual(post_user_input_message, "Selected block device ")

        env.get_collaborators().prompter().on(
            "prompt_user_input_fn", str, faker.Anything, bool, PromptLevel, str
        ).side_effect = prompt_assertion_callback
        ImageBurnerCmdRunner()._prompt_for_block_device_name(env.get_collaborators())

    def test_download_image(self) -> None:
        env = TestEnv.create()
        image_file_path = "/image/file/path"

        def download_file_assertion(
            url: str,
            download_folder: str,
            verify_already_downloaded: bool,
            progress_bar: bool,
        ) -> None:
            self.assertEqual(url, ARG_IMAGE_DOWNLOAD_URL)
            self.assertEqual(download_folder, ARG_IMAGE_DOWNLOAD_PATH)
            self.assertTrue(verify_already_downloaded)
            self.assertTrue(progress_bar)
            return image_file_path

        env.get_collaborators().http_client().on(
            "download_file_fn", str, str, bool, bool
        ).side_effect = download_file_assertion
        env.get_collaborators().summary().on("append", str, str).side_effect = lambda attribute_name, value: (
            self.assertEqual(attribute_name, "image_file_path"),
            self.assertEqual(value, image_file_path),
        )
        ImageBurnerCmdRunner()._download_image(
            env.get_context(),
            ARG_IMAGE_DOWNLOAD_URL,
            ARG_IMAGE_DOWNLOAD_PATH,
            env.get_collaborators(),
        )

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._burn_image_linux")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._run_pre_burn_approval_flow")
    def test_burn_image_by_os_linux(
        self,
        run_pre_burn_approval_flow_call: mock.MagicMock,
        burn_image_linux_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create(ctx=Context.create(os_arch=OsArch(os=LINUX)))
        ImageBurnerCmdRunner()._burn_image_by_os(
            env.get_context(),
            SELECTED_BLOCK_DEVICE,
            ARG_IMAGE_DOWNLOAD_PATH,
            env.get_collaborators(),
            self.create_fake_image_burner_args(),
        )
        run_pre_burn_approval_flow_call.assert_called_once()
        burn_image_linux_call.assert_called_once()

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._burn_image_darwin")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._run_pre_burn_approval_flow")
    def test_burn_image_by_os_darwin(
        self,
        run_pre_burn_approval_flow_call: mock.MagicMock,
        burn_image_darwin_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create(ctx=Context.create(os_arch=OsArch(os=MAC_OS)))
        ImageBurnerCmdRunner()._burn_image_by_os(
            env.get_context(),
            SELECTED_BLOCK_DEVICE,
            ARG_IMAGE_DOWNLOAD_PATH,
            env.get_collaborators(),
            self.create_fake_image_burner_args(),
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
                self.create_fake_image_burner_args(),
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
                self.create_fake_image_burner_args(),
            ),
        )

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._ask_to_verify_block_device")
    def test_run_pre_burn_approval_flow(self, ask_to_verify_block_device_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().summary().on("show_summary_and_prompt_for_enter", str).side_effect = (
            lambda title: self.assertEqual(title, f"Burning image to {SELECTED_BLOCK_DEVICE}")
        )
        ImageBurnerCmdRunner()._run_pre_burn_approval_flow(
            env.get_context(), SELECTED_BLOCK_DEVICE, env.get_collaborators()
        )
        ask_to_verify_block_device_call.assert_called_once()

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._configure_boot_partition_for_ssh")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._extract_image_file")
    def test_burn_image_linux(self, mock_extract: mock.MagicMock, mock_configure_boot: mock.MagicMock) -> None:
        # Mock the extraction to return the original file path
        mock_extract.return_value = (ARG_IMAGE_DOWNLOAD_PATH, None)
        
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, "Formatting block device and burning image..."
        )
        env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = (
            lambda args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str: self.assertEqual(
                args,
                [f"dd if={ARG_IMAGE_DOWNLOAD_PATH} of={SELECTED_BLOCK_DEVICE} bs=4M conv=fsync status=progress"],
            )
        )
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, "Flushing write-cache..."
        )
        env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = (
            lambda args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str: self.assertEqual(
                args, ["sync"]
            )
        )
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda msg: self.assertEqual(
            msg, "It is now safe to remove the SD-Card !"
        )
        ImageBurnerCmdRunner()._burn_image_linux(
            SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators(), self.create_fake_image_burner_args()
        )

    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._configure_boot_partition_for_ssh")
    @mock.patch(f"{SD_CARD_IMAGE_BURNER_RUNNER_PATH}._extract_image_file")
    def test_burn_image_darwin(self, mock_extract: mock.MagicMock, mock_configure_boot: mock.MagicMock) -> None:
        # Mock the extraction to return the original file path
        mock_extract.return_value = (ARG_IMAGE_DOWNLOAD_PATH, None)
        
        env = TestEnv.create()
        
        # Track the sequence of print calls
        print_calls = []
        def track_print(msg):
            print_calls.append(msg)
            return None  # Return value for print
            
        env.get_collaborators().printer().on("print_fn", str).side_effect = track_print
        
        # Track the sequence of process calls
        process_calls = []
        def track_process(args, working_dir=None, fail_msg=None, fail_on_error=None, allow_single_shell_command_str=None):
            process_calls.append(args)
            return "DRY_RUN_OUTPUT"  # Return value for process
            
        env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = track_process
        
        ImageBurnerCmdRunner()._burn_image_darwin(
            SELECTED_BLOCK_DEVICE, ARG_IMAGE_DOWNLOAD_PATH, env.get_collaborators(), self.create_fake_image_burner_args()
        )
        
        # Verify the expected print messages (ignoring the colored password message)
        expected_prints = [
            "Unmounting selected block device (SD-Card)...",
            "Formatting block device and burning a new image (Press Ctrl+T to show progress)...",
            # Skip the colored password message
            "Flushing write-cache to block device...",
            f"Remounting block device {SELECTED_BLOCK_DEVICE}...",
            f"Ejecting block device {SELECTED_BLOCK_DEVICE}...",
            "It is now safe to remove the SD-Card !"
        ]
        
        # Filter out the colored password message
        filtered_prints = [msg for msg in print_calls if not msg.startswith('\x1b[0;33m')]
        
        self.assertEqual(filtered_prints, expected_prints)
        
        # Verify the expected process calls
        expected_processes = [
            ["diskutil", "unmountDisk", SELECTED_BLOCK_DEVICE],
            [f"sudo dd if={ARG_IMAGE_DOWNLOAD_PATH} of={SELECTED_BLOCK_DEVICE_DARWIN} bs=1m conv=sync status=progress"],
            ["sync"],
            ["diskutil", "unmountDisk", SELECTED_BLOCK_DEVICE],
            ["diskutil", "mountDisk", SELECTED_BLOCK_DEVICE],
            ["diskutil", "eject", SELECTED_BLOCK_DEVICE]
        ]
        
        self.assertEqual(process_calls, expected_processes)

    def test_read_block_devices_darwin_success(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = (
            lambda args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str: self.assertEqual(
                args, ["diskutil", "list"]
            )
        )
        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os=MAC_OS)),
                env.get_collaborators(),
            ),
        )

    def test_read_block_devices_linux_success(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = (
            lambda args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str: self.assertEqual(
                args, ["lsblk", "-p"]
            )
        )
        Assertion.expect_success(
            self,
            method_to_run=lambda: ImageBurnerCmdRunner()._read_block_devices(
                Context.create(os_arch=OsArch(os=LINUX)),
                env.get_collaborators(),
            ),
        )

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
        env.get_collaborators().prompter().on("prompt_yes_no_fn", str, PromptLevel, str, str).side_effect = (
            lambda message, level, post_yes_message, post_no_message: (
                self.assertIn(
                    f"ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE '{SELECTED_BLOCK_DEVICE}'",
                    message,
                ),
                self.assertEqual(level, PromptLevel.CRITICAL),
                self.assertEqual(post_no_message, "Aborted by user."),
                self.assertEqual(post_yes_message, "Block device was approved by user"),
            )
        )
        ImageBurnerCmdRunner()._ask_to_verify_block_device(SELECTED_BLOCK_DEVICE, env.get_collaborators())
