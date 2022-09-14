#!/usr/bin/env python3

import os
from typing import Any
from loguru import logger
from external.python_scripts_lib.utils.httpclient import HttpClient
from external.python_scripts_lib.utils.patterns import Patterns
from external.python_scripts_lib.utils.properties import Properties
from external.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.utils.process import Process
from external.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.utils.checks import Checks
from external.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.utils.prompter import PromptLevel, Prompter
from external.python_scripts_lib.colors import color

PATTERNS_FILE_PATH = "common/sd_card/patterns.properties"


class ImageBurnerArgs:

    image_download_url: str

    def __init__(self, download_url: str) -> None:
        self.image_download_url = download_url


class Collaborators:
    io: IOUtils
    process: Process
    checks: Checks
    printer = Printer
    prompter = Prompter
    properties = Properties
    patterns = Patterns
    http_client = HttpClient


class ImageBurnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils()
        self.process = Process.create(ctx)
        self.checks = Checks.create(ctx)
        self.printer = Printer.create(ctx)
        self.prompter = Prompter.create(ctx)
        self.properties = Properties.create(self.io)
        self.patterns = Patterns.create(self.io)
        self.http_client = HttpClient.create(ctx, self.io)


class ImageBurnerRunner:
    def run(self, ctx: Context, args: ImageBurnerArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside ImageBurner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks)

        collaborators.printer.print_fn("Please select a block device:\n")

        block_devices = self.read_block_devices(ctx=ctx, process=collaborators.process)
        if self.eval_step_failure(ctx, block_devices, "Cannot read block devices"):
            return

        collaborators.printer.print_fn(block_devices)

        block_device_name = self.select_block_device(prompter=collaborators.prompter)
        if self.eval_step_failure(ctx, block_device_name, "Block device was not selected, aborting"):
            return

        is_verified = self.verify_block_device_name(
            block_devices=block_devices, selected_block_device=block_device_name
        )
        if self.eval_step_failure(ctx, is_verified, "Block device is not part of the available block devices"):
            return

        should_continue = self.ask_to_verify_block_device(
            block_device_name=block_device_name, prompter=collaborators.prompter
        )
        if self.eval_step_failure(ctx, should_continue, "Aborted due to user request"):
            return

        image_file_path = self.download_image(
            args.image_download_url, collaborators.http_client, collaborators.patterns, collaborators.printer
        )

        if self.eval_step_failure(ctx, image_file_path, "Failed to download image to burn"):
            return

        logger.debug(f"Burn image candidate is located at path: {image_file_path}")

        success = self.burn_image(
            ctx,
            block_device_name,
            image_file_path,
            collaborators.process,
            collaborators.prompter,
            collaborators.printer,
        )
        if self.eval_step_failure(ctx, success, "Failed burning an image"):
            return

    def eval_step_failure(self, ctx: Context, step_response: Any, err_msg: str) -> bool:
        result = False
        if ctx.is_dry_run():
            # On dry run, allow running all step commands
            return result

        if not step_response:
            logger.critical(err_msg)
            result = True

        return result

    def download_image(
        self,
        image_download_url: str,
        http_client: HttpClient,
        patterns: Patterns,
        printer: Printer,
    ) -> str:
        download_folder = self.resolve_pattern(patterns, "sd_card.image.download.path")
        filename = os.path.basename(image_download_url)
        printer.print_fn(f"Downloading image to burn. file: {filename}")
        return http_client.download_file_fn(
            url=image_download_url,
            download_folder=download_folder,
            verify_already_downloaded=True,
            progress_bar=True,
        )

    def burn_image(
        self,
        ctx: Context,
        block_device_name: str,
        burn_image_file_path: str,
        process: Process,
        prompter: Prompter,
        printer: Printer,
    ) -> bool:

        success = False
        if ctx.os_arch.is_linux():
            printer.print_fn(template_logo_install())
            printer.print_fn(template_instructions(block_device_name, burn_image_file_path))
            success = self.burn_image_linux(block_device_name, burn_image_file_path, process, prompter, printer)

        elif ctx.os_arch.is_darwin():
            printer.print_fn(template_logo_install())
            printer.print_fn(template_instructions(block_device_name, burn_image_file_path))
            success = self.burn_image_darwin(block_device_name, burn_image_file_path, process, prompter, printer)

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")

        return success

    def burn_image_linux(
        self, block_device_name: str, burn_image_file_path: str, process: Process, prompter: Prompter, printer: Printer
    ) -> bool:

        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        should_format = prompter.prompt_yes_no_fn(
            f"\nARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE '{block_device_name}'", PromptLevel.CRITICAL
        )
        if not should_format:
            logger.critical("Stopping installation process. reason: aborted by user")
            return False

        printer.print_fn("Formatting block device and burning a new image...")
        process.run_fn(
            allow_single_shell_command_str=True,
            args=[f"unzip -p {burn_image_file_path} | dd of={block_device_name} bs=4M conv=fsync status=progress"],
        )

        printer.print_fn("Flushing write-cache...")
        process.run_fn(args=["sync"])

        # TODO: allow SSH access and eject disk on Linux

        printer.print_fn("It is now safe to remove the SD-Card !")
        return True

    def burn_image_darwin(
        self, block_device_name: str, burn_image_file_path: str, process: Process, prompter: Prompter, printer: Printer
    ) -> bool:

        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        # Use non-buffered RAW disk (rdisk) when available for higher R/W speed
        # rdiskX is closer to the physical disk than the buffered cache one diskX
        raw_block_device_name = None
        yes_no_message = f"\nARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE {block_device_name}"
        if "/dev/" in block_device_name:
            # Replace dev/ with dev/r
            # Example: /dev/disk2 --> /dev/rdisk2
            raw_block_device_name = block_device_name.replace("/dev/", "/dev/r", 1)
            yes_no_message += f"(Raw disk {raw_block_device_name})"

        should_format = prompter.prompt_yes_no_fn(yes_no_message, PromptLevel.CRITICAL)
        if not should_format:
            logger.critical("Stopping installation process. reason: aborted by user")
            return False

        printer.print_fn("Unmounting selected block device (SD-Card)...")
        process.run_fn(args=["diskutil", "unmountDisk", block_device_name])

        printer.print_fn("Formatting block device and burning a new image (Press Ctrl+T to show progress)...")

        blk_device_name = raw_block_device_name if raw_block_device_name else block_device_name
        format_bs_cmd = [f"unzip -p {burn_image_file_path} | sudo dd of={blk_device_name} bs=1m"]
        process.run_fn(
            allow_single_shell_command_str=True,
            args=format_bs_cmd,
        )

        printer.print_fn("Flushing write-cache to block device...")
        process.run_fn(args=["sync"])

        printer.print_fn(f"Remounting block device {block_device_name}...")
        process.run_fn(args=["diskutil", "unmountDisk", block_device_name])
        process.run_fn(args=["diskutil", "mountDisk", block_device_name])

        printer.print_fn("Allowing SSH access...")
        process.run_fn(args=["sudo", "touch", "/Volumes/boot/ssh"])

        printer.print_fn(f"Ejecting block device {block_device_name}...")
        process.run_fn(args=["diskutil", "eject", block_device_name])

        printer.print_fn("It is now safe to remove the SD-Card !")
        return True

    def verify_block_device_name(self, block_devices: str, selected_block_device: str) -> bool:
        if selected_block_device in block_devices:
            logger.debug("Identified a valid block device. name: {}", selected_block_device)
            return True
        else:
            logger.debug("Invalid block device. name: {}", selected_block_device)
            return False

    def ask_to_verify_block_device(self, block_device_name: str, prompter: Prompter) -> bool:
        logger.debug("Asking user to verify selected block device")
        message = "\nIS THIS THE CHOSEN BLOCK DEVICE - {}".format(block_device_name)
        return prompter.prompt_yes_no_fn(message, PromptLevel.CRITICAL)

    def select_block_device(self, prompter: Prompter) -> str:
        logger.debug("Prompting user to select a block device name")
        return prompter.prompt_user_input_fn("Type block device name")

    def read_block_devices(self, ctx: Context, process: Process) -> str:
        logger.debug("Printing available block devices")
        output = ""
        if ctx.os_arch.is_linux():
            output = process.run_fn(args=["lsblk", "-p"])

        elif ctx.os_arch.is_darwin():
            output = process.run_fn(args=["diskutil", "list"])

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")

        return output

    def resolve_pattern(self, patterns: Patterns, key: str) -> str:
        return patterns.resolve_pattern_fn(PATTERNS_FILE_PATH, key)

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("lsblk")
            checks.check_tool_fn("unzip")
            checks.check_tool_fn("dd")
            checks.check_tool_fn("sync")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("diskutil")
            checks.check_tool_fn("unzip")
            checks.check_tool_fn("dd")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def template_logo_install() -> str:
    return f"""
██╗███╗   ███╗ █████╗  ██████╗ ███████╗    ██████╗ ██╗   ██╗██████╗ ███╗   ██╗███████╗██████╗ 
██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝    ██╔══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝██╔══██╗
██║██╔████╔██║███████║██║  ███╗█████╗      ██████╔╝██║   ██║██████╔╝██╔██╗ ██║█████╗  ██████╔╝
██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝      ██╔══██╗██║   ██║██╔══██╗██║╚██╗██║██╔══╝  ██╔══██╗
██║██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗    ██████╔╝╚██████╔╝██║  ██║██║ ╚████║███████╗██║  ██║
╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
"""


def template_instructions(block_device_name: str, image_name: str) -> str:
    return f"""
  ================================================================================================
  This script burns an image on an SD-Card. The card can be used as a block device.

    • Block Device...: {block_device_name}
    • Image Name.....: {image_name}

  {color.YELLOW}Elevated user permissions might be required for this step !{color.NONE}

  The content of the SD-Card will be formatted, {color.RED}it is an irreversible process !{color.NONE}
  ================================================================================================
"""
