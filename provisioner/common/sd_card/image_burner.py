#!/usr/bin/env python3

import os

from loguru import logger

from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.httpclient import HttpClient
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.json_util import JsonUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.process import Process
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import (
    ProgressIndicator,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.prompter import (
    Prompter,
    PromptLevel,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.summary import Summary


class ImageBurnerArgs:

    image_download_url: str
    image_download_path: str

    def __init__(self, download_url: str, download_path: str) -> None:
        self.image_download_url = download_url
        self.image_download_path = download_path


class Collaborators:
    io: IOUtils
    process: Process
    summary: Summary
    checks: Checks
    printer = Printer
    prompter = Prompter
    http_client = HttpClient


class ImageBurnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.process = Process.create(ctx)
        self.json_util = JsonUtil.create(ctx, self.io)
        self.checks = Checks.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.http_client = HttpClient.create(ctx, self.io, self.printer)
        self.summary = Summary.create(ctx, self.json_util, self.printer, self.prompter)


class ImageBurnerCmdRunner:
    def run(self, ctx: Context, args: ImageBurnerArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside ImageBurner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks)
        self._print_pre_run_instructions(collaborators.printer, collaborators.prompter)

        block_device_name = self._select_block_device(
            ctx,
            collaborators.process,
            collaborators.prompter,
            collaborators.printer,
            collaborators.summary,
        )
        collaborators.summary.add_value("block_device_name", block_device_name)

        collaborators.printer.new_line_fn()
        image_file_path = Evaluator.eval_step_failure_throws(
            call=lambda: self._download_image(
                args.image_download_url, args.image_download_path, collaborators.http_client
            ),
            ctx=ctx,
            err_msg="Failed to download image to burn",
        )
        collaborators.summary.add_value("image_file_path", image_file_path)

        logger.debug(f"Burn image candidate is located at path: {image_file_path}")

        Evaluator.eval_step_failure_throws(
            call=lambda: self._burn_image(
                ctx,
                block_device_name,
                image_file_path,
                collaborators.process,
                collaborators.summary,
                collaborators.prompter,
                collaborators.printer,
            ),
            ctx=ctx,
            err_msg="Failed burning an image",
        )

    def _select_block_device(
        self, ctx: Context, process: Process, prompter: Prompter, printer: Printer) -> str:

        printer.print_fn("Please select a block device:")
        printer.new_line_fn()

        block_devices = Evaluator.eval_step_failure_throws(
            call=lambda: self.read_block_devices(ctx=ctx, process=process),
            ctx=ctx,
            err_msg="Cannot read block devices",
        )

        logger.debug("Printing available block devices")
        printer.print_fn(block_devices)

        block_device_name = Evaluator.eval_step_failure_throws(
            call=lambda: self.select_block_device(prompter=prompter),
            ctx=ctx,
            err_msg="Block device was not selected, aborting",
        )

        Evaluator.eval_step_failure_throws(
            call=lambda: self.verify_block_device_name(
                block_devices=block_devices, selected_block_device=block_device_name
            ),
            ctx=ctx,
            err_msg=f"Block device is not part of the available block devices. name: {block_device_name}",
        )

        return block_device_name

    def _download_image(
        self,
        image_download_url: str,
        image_download_path: str,
        http_client: HttpClient,
    ) -> str:
        filename = os.path.basename(image_download_url)
        logger.debug(f"Downloading image to burn. file: {filename}")
        return http_client.download_file_fn(
            url=image_download_url,
            download_folder=image_download_path,
            verify_already_downloaded=True,
            progress_bar=True,
        )

    def _burn_image(
        self,
        ctx: Context,
        block_device_name: str,
        burn_image_file_path: str,
        process: Process,
        summary: Summary,
        prompter: Prompter,
        printer: Printer,
    ):

        if ctx.os_arch.is_linux():
            self._run_pre_burn_approval_flow(ctx, block_device_name, prompter, summary)
            Evaluator.eval_step_failure_throws(
                call=lambda: self._burn_image_linux(block_device_name, burn_image_file_path, process, prompter, printer),
                ctx=ctx,
                err_msg="Failed to burn image",
            )

        elif ctx.os_arch.is_darwin():
            self._run_pre_burn_approval_flow(ctx, block_device_name, prompter, summary)
            Evaluator.eval_step_failure_throws(
                call=lambda: self._burn_image_darwin(
                    block_device_name, burn_image_file_path, process, prompter, printer
                ),
                ctx=ctx,
                err_msg="Failed to burn image",
            )

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")

        return

    def _run_pre_burn_approval_flow(self, ctx: Context, block_device_name: str, prompter: Prompter, summary: Summary):
        summary.show_summary_and_prompt_for_enter(f"Burning image to {block_device_name}")
        Evaluator.eval_step_failure_throws(
            call=lambda: self.ask_to_verify_block_device(block_device_name=block_device_name, prompter=prompter),
            ctx=ctx,
            err_msg="Aborted upon user request",
        )

    def _burn_image_linux(
        self, block_device_name: str, burn_image_file_path: str, process: Process, prompter: Prompter, printer: Printer
    ):

        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        printer.print_fn("Formatting block device and burning a new image...")
        process.run_fn(
            allow_single_shell_command_str=True,
            args=[f"unzip -p {burn_image_file_path} | dd of={block_device_name} bs=4M conv=fsync status=progress"],
        )

        printer.print_fn("Flushing write-cache...")
        process.run_fn(args=["sync"])

        # TODO: allow SSH access and eject disk on Linux

        printer.print_fn("It is now safe to remove the SD-Card !")

    def _burn_image_darwin(
        self, block_device_name: str, burn_image_file_path: str, process: Process, prompter: Prompter, printer: Printer
    ):

        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        # Use non-buffered RAW disk (rdisk) when available for higher R/W speed
        # rdiskX is closer to the physical disk than the buffered cache one diskX
        raw_block_device_name = None
        if "/dev/" in block_device_name:
            # Replace dev/ with dev/r
            # Example: /dev/disk2 --> /dev/rdisk2
            raw_block_device_name = block_device_name.replace("/dev/", "/dev/r", 1)

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

    def verify_block_device_name(self, block_devices: str, selected_block_device: str) -> bool:
        if selected_block_device in block_devices:
            logger.debug("Identified a valid block device. name: {}", selected_block_device)
            return True
        else:
            logger.debug("Invalid block device. name: {}", selected_block_device)
            return False

    def ask_to_verify_block_device(self, block_device_name: str, prompter: Prompter) -> bool:
        logger.debug("Asking user to verify selected block device before format")
        return prompter.prompt_yes_no_fn(
            f"ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE '{block_device_name}'",
            level=PromptLevel.CRITICAL,
            post_no_message="Aborted by user.",
            post_yes_message="Block device was approved by user",
        )

    def select_block_device(self, prompter: Prompter) -> str:
        logger.debug("Prompting user to select a block device name")
        return prompter.prompt_user_input_fn(
            message="Type block device name", post_user_input_message="Selected block device :: "
        )

    def read_block_devices(self, ctx: Context, process: Process) -> str:
        logger.debug("Reading available block devices")
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

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
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

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(generate_logo_image_burner())
        printer.print_with_rich_table_fn(generate_instructions_pre_image_burn())
        prompter.prompt_for_enter_fn()


def generate_logo_image_burner() -> str:
    return f"""
██╗███╗   ███╗ █████╗  ██████╗ ███████╗    ██████╗ ██╗   ██╗██████╗ ███╗   ██╗███████╗██████╗ 
██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝    ██╔══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝██╔══██╗
██║██╔████╔██║███████║██║  ███╗█████╗      ██████╔╝██║   ██║██████╔╝██╔██╗ ██║█████╗  ██████╔╝
██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝      ██╔══██╗██║   ██║██╔══██╗██║╚██╗██║██╔══╝  ██╔══██╗
██║██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗    ██████╔╝╚██████╔╝██║  ██║██║ ╚████║███████╗██║  ██║
╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝"""


def generate_instructions_pre_image_burn() -> str:
    return f"""
  Select a block device to burn an image onto (example: SD-Card or HDD)

  [yellow]Elevated user permissions might be required for this step ![/yellow]

  The content of the block device will be formatted, [red]it is an irreversible process ![/red]
"""
