#!/usr/bin/env python3


from loguru import logger
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.prompter import PromptLevel


class ImageBurnerArgs:

    image_download_url: str
    image_download_path: str

    def __init__(self, image_download_url: str, image_download_path: str) -> None:
        self.image_download_url = image_download_url
        self.image_download_path = image_download_path


class ImageBurnerCmdRunner:
    def run(self, ctx: Context, args: ImageBurnerArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside ImageBurner run()")
        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators)
        block_device_name = self._select_block_device(ctx, collaborators)
        image_file_path = self._download_image(ctx, args.image_download_url, args.image_download_path, collaborators)
        self._burn_image_by_os(ctx, block_device_name, image_file_path, collaborators)

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

    def _select_block_device(self, ctx: Context, collaborators: CoreCollaborators) -> str:
        collaborators.printer().print_fn("Block device selection:")
        collaborators.printer().new_line_fn()
        block_devices_output = self._print_and_return_block_devices_output(ctx, collaborators)
        return self._ask_user_to_select_block_devices(
            ctx=ctx, collaborators=collaborators, block_devices_output=block_devices_output
        )

    def _print_and_return_block_devices_output(self, ctx: Context, collaborators: CoreCollaborators) -> str:
        block_devices = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self._read_block_devices(ctx=ctx, collaborators=collaborators),
            ctx=ctx,
            err_msg="Cannot read block devices",
        )
        logger.debug("Printing available block devices")
        collaborators.printer().print_fn(block_devices)
        return block_devices

    def _read_block_devices(self, ctx: Context, collaborators: CoreCollaborators) -> str:
        logger.debug("Reading available block devices")
        output = ""
        if ctx.os_arch.is_linux():
            output = collaborators.process().run_fn(args=["lsblk", "-p"])

        elif ctx.os_arch.is_darwin():
            output = collaborators.process().run_fn(args=["diskutil", "list"])

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")

        return output

    def _ask_user_to_select_block_devices(
        self, ctx: Context, collaborators: CoreCollaborators, block_devices_output: str
    ) -> str:

        block_device_name = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self._prompt_for_block_device_name(collaborators=collaborators),
            ctx=ctx,
            err_msg="Block device was not selected, aborting",
        )

        Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self._verify_block_device_name(
                block_devices=block_devices_output, selected_block_device=block_device_name
            ),
            ctx=ctx,
            err_msg=f"Block device is not part of the available block devices. name: {block_device_name}",
        )

        collaborators.printer().new_line_fn()
        collaborators.summary().append("block_device_name", block_device_name)
        return block_device_name

    def _verify_block_device_name(self, block_devices: str, selected_block_device: str) -> bool:
        if selected_block_device in block_devices:
            logger.debug("Identified a valid block device. name: {}", selected_block_device)
            return True
        else:
            logger.debug("Invalid block device. name: {}", selected_block_device)
            return False

    def _prompt_for_block_device_name(self, collaborators: CoreCollaborators) -> str:
        logger.debug("Prompting user to select a block device name")
        collaborators.printer().print_fn("Please select a block device:")
        collaborators.printer().new_line_fn()
        return collaborators.prompter().prompt_user_input_fn(
            message="Type block device name", post_user_input_message="Selected block device :: "
        )

    def _download_image(
        self,
        ctx: Context,
        image_download_url: str,
        image_download_path: str,
        collaborators: CoreCollaborators,
    ) -> str:

        image_file_path = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: collaborators.http_client().download_file_fn(
                url=image_download_url,
                download_folder=image_download_path,
                verify_already_downloaded=True,
                progress_bar=True,
            ),
            ctx=ctx,
            err_msg="Failed to download image to burn",
        )
        logger.debug(f"Burn image candidate is located at path: {image_file_path}")
        collaborators.summary().append("image_file_path", image_file_path)
        return image_file_path

    def _burn_image_by_os(
        self,
        ctx: Context,
        block_device_name: str,
        burn_image_file_path: str,
        collaborators: CoreCollaborators,
    ):

        if ctx.os_arch.is_linux():
            self._run_pre_burn_approval_flow(ctx, block_device_name, collaborators)
            self._burn_image_linux(block_device_name, burn_image_file_path, collaborators)

        elif ctx.os_arch.is_darwin():
            self._run_pre_burn_approval_flow(ctx, block_device_name, collaborators)
            self._burn_image_darwin(block_device_name, burn_image_file_path, collaborators)

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")

        return

    def _run_pre_burn_approval_flow(self, ctx: Context, block_device_name: str, collaborators: CoreCollaborators):
        collaborators.summary().show_summary_and_prompt_for_enter(f"Burning image to {block_device_name}")
        Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: self._ask_to_verify_block_device(
                block_device_name=block_device_name, collaborators=collaborators
            ),
            ctx=ctx,
            err_msg="Aborted upon user request",
        )

    def _ask_to_verify_block_device(self, block_device_name: str, collaborators: CoreCollaborators) -> bool:
        logger.debug("Asking user to verify selected block device before format")
        return collaborators.prompter().prompt_yes_no_fn(
            f"ARE YOU SURE YOU WANT TO FORMAT BLOCK DEVICE '{block_device_name}'",
            level=PromptLevel.CRITICAL,
            post_no_message="Aborted by user.",
            post_yes_message="Block device was approved by user",
        )

    def _burn_image_linux(self, block_device_name: str, burn_image_file_path: str, collaborators: CoreCollaborators):

        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        collaborators.printer().print_fn("Formatting block device and burning a new image...")
        collaborators.process().run_fn(
            allow_single_shell_command_str=True,
            args=[f"unzip -p {burn_image_file_path} | dd of={block_device_name} bs=4M conv=fsync status=progress"],
        )

        collaborators.printer().print_fn("Flushing write-cache...")
        collaborators.process().run_fn(args=["sync"])

        # TODO: allow SSH access and eject disk on Linux

        collaborators.printer().print_fn("It is now safe to remove the SD-Card !")

    def _burn_image_darwin(self, block_device_name: str, burn_image_file_path: str, collaborators: CoreCollaborators):

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

        collaborators.printer().print_fn("Unmounting selected block device (SD-Card)...")
        collaborators.process().run_fn(args=["diskutil", "unmountDisk", block_device_name])

        collaborators.printer().print_fn(
            "Formatting block device and burning a new image (Press Ctrl+T to show progress)..."
        )

        blk_device_name = raw_block_device_name if raw_block_device_name else block_device_name
        format_bs_cmd = [f"unzip -p {burn_image_file_path} | sudo dd of={blk_device_name} bs=1m"]
        collaborators.process().run_fn(
            allow_single_shell_command_str=True,
            args=format_bs_cmd,
        )

        collaborators.printer().print_fn("Flushing write-cache to block device...")
        collaborators.process().run_fn(args=["sync"])

        collaborators.printer().print_fn(f"Remounting block device {block_device_name}...")
        collaborators.process().run_fn(args=["diskutil", "unmountDisk", block_device_name])
        collaborators.process().run_fn(args=["diskutil", "mountDisk", block_device_name])

        collaborators.printer().print_fn("Allowing SSH access...")
        collaborators.process().run_fn(args=["sudo", "touch", "/Volumes/boot/ssh"])

        collaborators.printer().print_fn(f"Ejecting block device {block_device_name}...")
        collaborators.process().run_fn(args=["diskutil", "eject", block_device_name])

        collaborators.printer().print_fn("It is now safe to remove the SD-Card !")

    def _print_pre_run_instructions(self, collaborators: CoreCollaborators):
        collaborators.printer().print_fn(generate_logo_image_burner())
        collaborators.printer().print_with_rich_table_fn(generate_instructions_pre_image_burn())
        collaborators.prompter().prompt_for_enter_fn()


def generate_logo_image_burner() -> str:
    return """
██╗███╗   ███╗ █████╗  ██████╗ ███████╗    ██████╗ ██╗   ██╗██████╗ ███╗   ██╗███████╗██████╗
██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝    ██╔══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝██╔══██╗
██║██╔████╔██║███████║██║  ███╗█████╗      ██████╔╝██║   ██║██████╔╝██╔██╗ ██║█████╗  ██████╔╝
██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝      ██╔══██╗██║   ██║██╔══██╗██║╚██╗██║██╔══╝  ██╔══██╗
██║██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗    ██████╔╝╚██████╔╝██║  ██║██║ ╚████║███████╗██║  ██║
╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝"""


def generate_instructions_pre_image_burn() -> str:
    return """
  Select a block device to burn an image onto (example: SD-Card or HDD)

  [yellow]Elevated user permissions might be required for this step ![/yellow]

  The content of the block device will be formatted, [red]it is an irreversible process ![/red]
"""
