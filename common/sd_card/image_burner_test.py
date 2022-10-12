#!/usr/bin/env python3

import unittest
from unittest import mock
from common.sd_card.image_burner import ImageBurnerArgs, ImageBurnerRunner, Collaborators

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    MissingUtilityException,
    CliApplicationException,
    StepEvaluationFailure,
)
from external.python_scripts_lib.python_scripts_lib.utils.httpclient_fakes import FakeHttpClient
from external.python_scripts_lib.python_scripts_lib.utils.os import WINDOWS, LINUX, MAC_OS, OsArch
from external.python_scripts_lib.python_scripts_lib.utils.io_utils_fakes import FakeIOUtils
from external.python_scripts_lib.python_scripts_lib.utils.checks_fakes import FakeChecks
from external.python_scripts_lib.python_scripts_lib.utils.process_fakes import FakeProcess
from external.python_scripts_lib.python_scripts_lib.utils.prompter_fakes import FakePrompter
from external.python_scripts_lib.python_scripts_lib.utils.printer_fakes import FakePrinter
from external.python_scripts_lib.python_scripts_lib.utils.httpclient import HttpClient
from external.python_scripts_lib.python_scripts_lib.test_lib.assertions import Assertion
from external.python_scripts_lib.python_scripts_lib.utils.prompter import PromptLevel, Prompter


#
# To run these directly from the terminal use:
#  poetry run rpi --dry-run --verbose --auto-prompt os install
#
# To run as a single test target:
#  poetry run coverage run -m pytest common/sd_card/image_burner_test.py
#
class FakeCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        print("Creating Fake collaborators...")
        self.io = FakeIOUtils.create(ctx)
        self.process = FakeProcess.create(ctx)
        self.checks = FakeChecks.create(ctx)
        self.prompter = FakePrompter.create(ctx)
        self.printer = FakePrinter.create(ctx)
        self.http_client = FakeHttpClient.create(ctx, self.io)


class ImageBurnerTestShould(unittest.TestCase):
    def create_fake_collaborators(self, ctx: Context) -> FakeCollaborators:
        return FakeCollaborators(ctx)

    def test_prerequisites_fail_missing_utility(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        Assertion.expect_failure(
            self, ex_type=MissingUtilityException, methodToRun=lambda: runner.prerequisites(ctx, cols.checks)
        )

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("diskutil")
        cols.checks.register_utility("unzip")
        cols.checks.register_utility("dd")
        runner = ImageBurnerRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("lsblk")
        cols.checks.register_utility("unzip")
        cols.checks.register_utility("dd")
        cols.checks.register_utility("sync")
        runner = ImageBurnerRunner()
        Assertion.expect_success(self, methodToRun=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        runner = ImageBurnerRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )
        runner = ImageBurnerRunner()
        Assertion.expect_failure(self, ex_type=NotImplementedError, methodToRun=lambda: runner.prerequisites(ctx, None))

    def test_read_block_device_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.process.register_command(
            cmd_str="lsblk -p",
            expected_output="linux block devices",
        )
        runner = ImageBurnerRunner()
        output = Assertion.expect_success(self, methodToRun=lambda: runner.read_block_devices(ctx, cols.process))
        self.assertEqual(output, "linux block devices")

    def test_read_block_device_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.process.register_command(
            cmd_str="diskutil list",
            expected_output="darwin block devices",
        )
        runner = ImageBurnerRunner()
        output = Assertion.expect_success(self, methodToRun=lambda: runner.read_block_devices(ctx, cols.process))
        self.assertEqual(output, "darwin block devices")

    def test_read_block_device_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        Assertion.expect_failure(
            self, ex_type=NotImplementedError, methodToRun=lambda: runner.read_block_devices(ctx, cols.process)
        )

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )

        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        Assertion.expect_failure(
            self, ex_type=NotImplementedError, methodToRun=lambda: runner.read_block_devices(ctx, cols.process)
        )

    def test_burn_image_linux_skip_by_user(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        block_device_name = "test-block-device"
        os_image_file_path = "/path/to/image/file"

        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE", False)

        runner = ImageBurnerRunner()
        result = runner.burn_image_linux(
            block_device_name, os_image_file_path, cols.process, cols.prompter, cols.printer
        )
        self.assertFalse(result)

    def test_burn_image_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        block_device_name = "test-block-device"
        os_image_file_path = "/path/to/image/file"

        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE", True)
        cols.process.register_command(
            cmd_str=f"unzip -p {os_image_file_path} | dd of={block_device_name} bs=4M conv=fsync status=progress",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"sync",
            expected_output="",
        )

        runner = ImageBurnerRunner()
        result = runner.burn_image_linux(
            block_device_name, os_image_file_path, cols.process, cols.prompter, cols.printer
        )
        self.assertTrue(result)

    def test_burn_image_darwin_skip_by_user(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        block_device_name = "test-block-device/dev/"
        os_image_file_path = "/path/to/image/file"

        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE", False)

        runner = ImageBurnerRunner()
        result = runner.burn_image_darwin(
            block_device_name, os_image_file_path, cols.process, cols.prompter, cols.printer
        )
        self.assertFalse(result)

    def test_burn_image_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        block_device_name = "test-block-device/dev/"
        raw_block_device_name = "test-block-device/dev/r"
        os_image_file_path = "/path/to/image/file"

        cols = self.create_fake_collaborators(ctx)
        cols.prompter.register_yes_no_prompt("ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE", True)
        cols.process.register_command(
            cmd_str=f"diskutil unmountDisk {block_device_name}",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"unzip -p {os_image_file_path} | sudo dd of={raw_block_device_name} bs=1m",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"sync",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"diskutil unmountDisk {block_device_name}",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"diskutil mountDisk {block_device_name}",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"sudo touch /Volumes/boot/ssh",
            expected_output="",
        )
        cols.process.register_command(
            cmd_str=f"diskutil eject {block_device_name}",
            expected_output="",
        )

        runner = ImageBurnerRunner()
        result = runner.burn_image_darwin(
            block_device_name, os_image_file_path, cols.process, cols.prompter, cols.printer
        )
        self.assertTrue(result)

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.burn_image_linux")
    def test_burn_image_identify_linux(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))
        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        runner.burn_image(ctx, None, None, None, None, cols.printer)
        self.assertEqual(1, run_call.call_count)

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.burn_image_darwin")
    def test_burn_image_identify_darwin(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))
        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        runner.burn_image(ctx, None, None, None, None, cols.printer)
        self.assertEqual(1, run_call.call_count)

    @mock.patch("common.sd_card.image_burner.ImageBurnerRunner.burn_image_darwin")
    def test_burn_image_os_not_supported(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))
        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        Assertion.expect_failure(
            self,
            ex_type=NotImplementedError,
            methodToRun=lambda: runner.burn_image(ctx, None, None, None, None, cols.printer),
        )

        ctx = Context.create(os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"))
        cols = self.create_fake_collaborators(ctx)
        runner = ImageBurnerRunner()
        Assertion.expect_failure(
            self,
            ex_type=NotImplementedError,
            methodToRun=lambda: runner.burn_image(ctx, None, None, None, None, cols.printer),
        )

    def test_block_device_verification_fail(self) -> None:
        block_devices = ["/dev/disk1", "/dev/disk1"]
        runner = ImageBurnerRunner()
        self.assertFalse(runner.verify_block_device_name(block_devices, "/dev/disk3"))

    def test_block_device_verification_success(self) -> None:
        block_devices = ["/dev/disk1", "/dev/disk1"]
        runner = ImageBurnerRunner()
        self.assertTrue(runner.verify_block_device_name(block_devices, "/dev/disk1"))

    def test_burn_image_run_fail_on_prerequisites(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites:
            prerequisites.side_effect = CliApplicationException("runner failure")
            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=CliApplicationException,
                methodToRun=lambda: runner.run(ctx=ctx, args=None, collaborators=cols),
            )
            self.assertEqual(1, prerequisites.call_count)
            prerequisites.assert_called_once_with(ctx=ctx, checks=cols.checks)

    def test_burn_image_run_fail_to_read_block_devices(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices:

            prerequisites.return_value = True
            read_block_devices.return_value = False

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(ctx=ctx, args=None, collaborators=cols),
            )
            self.assertEqual(1, read_block_devices.call_count)
            read_block_devices.assert_called_once_with(ctx=ctx, process=cols.process)

    def test_burn_image_run_fail_to_select_block_devices(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices, mock.patch.object(ImageBurnerRunner, "select_block_device") as select_block_device:

            prerequisites.return_value = True
            read_block_devices.return_value = True
            select_block_device.return_value = False

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(ctx=ctx, args=None, collaborators=cols),
            )
            self.assertEqual(1, select_block_device.call_count)
            select_block_device.assert_called_once_with(prompter=cols.prompter)

    def test_burn_image_run_fail_to_verify_block_devices(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices, mock.patch.object(
            ImageBurnerRunner, "select_block_device"
        ) as select_block_device, mock.patch.object(
            ImageBurnerRunner, "verify_block_device_name"
        ) as verify_block_device_name:

            prerequisites.return_value = True
            read_block_devices.return_value = ["/dev/disk1", "/dev/disk2"]
            select_block_device.return_value = "/dev/disk3"
            verify_block_device_name.return_value = False

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(ctx=ctx, args=None, collaborators=cols),
            )
            self.assertEqual(1, verify_block_device_name.call_count)
            verify_block_device_name.assert_called_once_with(
                block_devices=["/dev/disk1", "/dev/disk2"], selected_block_device="/dev/disk3"
            )

    def test_burn_image_run_fail_to_ask_to_verify_block_devices(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices, mock.patch.object(
            ImageBurnerRunner, "select_block_device"
        ) as select_block_device, mock.patch.object(
            ImageBurnerRunner, "verify_block_device_name"
        ) as verify_block_device_name, mock.patch.object(
            ImageBurnerRunner, "ask_to_verify_block_device"
        ) as ask_to_verify_block_device:

            prerequisites.return_value = True
            read_block_devices.return_value = ["/dev/disk1", "/dev/disk2"]
            select_block_device.return_value = "/dev/disk1"
            verify_block_device_name.return_value = True
            ask_to_verify_block_device.return_value = False

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(ctx=ctx, args=None, collaborators=cols),
            )
            self.assertEqual(1, ask_to_verify_block_device.call_count)
            ask_to_verify_block_device.assert_called_once_with(block_device_name="/dev/disk1", prompter=cols.prompter)

    def test_burn_image_run_fail_to_download_image(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices, mock.patch.object(
            ImageBurnerRunner, "select_block_device"
        ) as select_block_device, mock.patch.object(
            ImageBurnerRunner, "verify_block_device_name"
        ) as verify_block_device_name, mock.patch.object(
            ImageBurnerRunner, "ask_to_verify_block_device"
        ) as ask_to_verify_block_device, mock.patch.object(
            ImageBurnerRunner, "download_image"
        ) as download_image:

            prerequisites.return_value = True
            read_block_devices.return_value = ["/dev/disk1", "/dev/disk2"]
            select_block_device.return_value = "/dev/disk1"
            verify_block_device_name.return_value = True
            ask_to_verify_block_device.return_value = True
            download_image.return_value = None

            image_download_url = "https://burn-image-test.download.com"
            image_download_path = "/path/to/downloaded/image"

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(
                    ctx=ctx, args=ImageBurnerArgs(image_download_url, image_download_path), collaborators=cols
                ),
            )
            self.assertEqual(1, download_image.call_count)
            download_image.assert_called_once_with(
                image_download_url, image_download_path, cols.http_client, cols.printer
            )

    def test_burn_image_run_fail_to_burn_image(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        with mock.patch.object(ImageBurnerRunner, "prerequisites") as prerequisites, mock.patch.object(
            ImageBurnerRunner, "read_block_devices"
        ) as read_block_devices, mock.patch.object(
            ImageBurnerRunner, "select_block_device"
        ) as select_block_device, mock.patch.object(
            ImageBurnerRunner, "verify_block_device_name"
        ) as verify_block_device_name, mock.patch.object(
            ImageBurnerRunner, "ask_to_verify_block_device"
        ) as ask_to_verify_block_device, mock.patch.object(
            ImageBurnerRunner, "download_image"
        ) as download_image, mock.patch.object(
            ImageBurnerRunner, "burn_image"
        ) as burn_image:

            prerequisites.return_value = True
            read_block_devices.return_value = ["/dev/disk1", "/dev/disk2"]
            select_block_device.return_value = "/dev/disk1"
            verify_block_device_name.return_value = True
            ask_to_verify_block_device.return_value = True
            download_image.return_value = "/path/to/image/file"
            burn_image.return_value = False

            cols = self.create_fake_collaborators(ctx)
            runner = ImageBurnerRunner()
            Assertion.expect_failure(
                self,
                ex_type=StepEvaluationFailure,
                methodToRun=lambda: runner.run(
                    ctx=ctx,
                    args=ImageBurnerArgs("https://burn-image-test.download.com", "/path/to/downloaded/image"),
                    collaborators=cols,
                ),
            )
            self.assertEqual(1, burn_image.call_count)
            burn_image.assert_called_once_with(
                ctx, "/dev/disk1", "/path/to/image/file", cols.process, cols.prompter, cols.printer
            )

    def test_verify_block_device_with_critical_prompt_level(self) -> None:
        fake_prompter = mock.MagicMock(name="prompter", spec=Prompter)
        fake_prompter.prompt_yes_no_fn.return_value = True

        block_device_name = "/dev/disk1"
        runner = ImageBurnerRunner()
        response = runner.ask_to_verify_block_device(block_device_name, fake_prompter)
        self.assertEqual(1, fake_prompter.prompt_yes_no_fn.call_count)
        self.assertTrue(response)

        fake_prompter.prompt_yes_no_fn.assert_called_once_with(
            f"\nIS THIS THE CHOSEN BLOCK DEVICE - {block_device_name}", PromptLevel.CRITICAL
        )

    def test_download_image_successfully(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        fake_http_client = mock.MagicMock(name="http-client", spec=HttpClient)

        download_url = "https://burn-image-test.com"
        download_path = "/path/to/downloaded/image"

        cols = self.create_fake_collaborators(ctx)

        runner = ImageBurnerRunner()
        path = runner.download_image(download_url, download_path, fake_http_client, cols.printer)

        fake_http_client.download_file_fn.assert_called_once_with(
            url=download_url,
            verify_already_downloaded=True,
            download_folder=download_path,
            progress_bar=True,
        )
