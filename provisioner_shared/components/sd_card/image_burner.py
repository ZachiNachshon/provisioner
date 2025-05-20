#!/usr/bin/env python3

import gzip
import lzma
import os
import shutil
import tempfile
import zipfile
from typing import Optional

from loguru import logger

from provisioner_shared.components.runtime.colors import colors
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks
from provisioner_shared.components.runtime.utils.prompter import PromptLevel


class ImageBurnerArgs:

    image_download_url: str
    image_download_path: str
    maybe_resources_path: str

    def __init__(
        self, image_download_url: str, image_download_path: str, maybe_resources_path: Optional[str] = None
    ) -> None:
        self.image_download_url = image_download_url
        self.image_download_path = image_download_path
        self.maybe_resources_path = maybe_resources_path


class ImageBurnerCmdRunner:
    def run(self, ctx: Context, args: ImageBurnerArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside ImageBurner run()")
        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators)
        block_device_name = self._select_block_device(ctx, collaborators)
        image_file_path = self._download_image(ctx, args.image_download_url, args.image_download_path, collaborators)
        self._burn_image_by_os(ctx, block_device_name, image_file_path, collaborators, args)

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("lsblk")
            checks.check_tool_fn("dd")
            checks.check_tool_fn("sync")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("diskutil")
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
            ctx=ctx,
            collaborators=collaborators,
            block_devices_output=block_devices_output,
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
                block_devices=block_devices_output,
                selected_block_device=block_device_name,
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
        collaborators.printer().new_line_fn()
        return collaborators.prompter().prompt_user_input_fn(
            message="Please type the block device name",
            post_user_input_message="Selected block device ",
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
        args: ImageBurnerArgs,
    ):

        if ctx.os_arch.is_linux():
            self._run_pre_burn_approval_flow(ctx, block_device_name, collaborators)
            self._burn_image_linux(block_device_name, burn_image_file_path, collaborators, args)

        elif ctx.os_arch.is_darwin():
            self._run_pre_burn_approval_flow(ctx, block_device_name, collaborators)
            self._burn_image_darwin(block_device_name, burn_image_file_path, collaborators, args)

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

    def _burn_image_darwin(
        self,
        block_device_name: str,
        burn_image_file_path: str,
        collaborators: CoreCollaborators,
        args: ImageBurnerArgs,
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

        collaborators.printer().print_fn("Unmounting selected block device (SD-Card)...")
        collaborators.process().run_fn(args=["diskutil", "unmountDisk", block_device_name])

        extracted_file_path, temp_dir = self._extract_image_file(burn_image_file_path, collaborators)

        try:
            collaborators.printer().print_fn(
                "Formatting block device and burning a new image (Press Ctrl+T to show progress)..."
            )
            collaborators.printer().print_fn(
                colors.color_text("Password is required for this step for sudo access !", colors.YELLOW)
            )

            blk_device_name = raw_block_device_name if raw_block_device_name else block_device_name
            collaborators.process().run_fn(
                allow_single_shell_command_str=True,
                args=[f"sudo dd if={extracted_file_path} of={blk_device_name} bs=1m conv=sync status=progress"],
            )

            collaborators.printer().print_fn("Flushing write-cache to block device...")
            collaborators.process().run_fn(args=["sync"])

            collaborators.printer().print_fn(f"Remounting block device {block_device_name}...")
            collaborators.process().run_fn(args=["diskutil", "unmountDisk", block_device_name])
            collaborators.process().run_fn(args=["diskutil", "mountDisk", block_device_name])

            # Configure SSH and first boot user
            self._configure_boot_partition_for_ssh(collaborators, args)

            collaborators.printer().print_fn(f"Ejecting block device {block_device_name}...")
            collaborators.process().run_fn(args=["diskutil", "eject", block_device_name])

            collaborators.printer().print_fn("It is now safe to remove the SD-Card !")
        finally:
            # Clean up temporary files if we created any
            if extracted_file_path != burn_image_file_path and temp_dir and os.path.exists(temp_dir):
                collaborators.io_utils().delete_directory_fn(temp_dir)

    def _burn_image_linux(
        self,
        block_device_name: str,
        burn_image_file_path: str,
        collaborators: CoreCollaborators,
        args: ImageBurnerArgs,
    ):
        logger.debug(
            f"About to format device and copy image to SD-Card. device: {block_device_name}, image: {burn_image_file_path}"
        )

        extracted_file_path, temp_dir = self._extract_image_file(burn_image_file_path, collaborators)

        try:
            collaborators.printer().print_fn("Formatting block device and burning image...")
            collaborators.process().run_fn(
                allow_single_shell_command_str=True,
                args=[f"dd if={extracted_file_path} of={block_device_name} bs=4M conv=fsync status=progress"],
            )

            collaborators.printer().print_fn("Flushing write-cache...")
            collaborators.process().run_fn(args=["sync"])

            # Configure SSH and first boot user
            self._configure_boot_partition_for_ssh(collaborators, args)

            collaborators.printer().print_fn("It is now safe to remove the SD-Card !")
        finally:
            # Clean up temporary files if we created any
            if extracted_file_path != burn_image_file_path and temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _configure_boot_partition_for_ssh(self, collaborators: CoreCollaborators, args: ImageBurnerArgs):
        """Configure the boot partition to enable SSH on first boot and set up the required configuration."""
        # Step 1: Find the Raspberry Pi boot partition
        boot_path = self._find_raspberry_pi_boot_partition(collaborators)
        if not boot_path:
            return

        # Step 2: Copy all files from the raspberrypi directory
        source_dir = args.maybe_resources_path
        if not source_dir:
            logger.debug("No resources path provided, skipping configuration files copy")
            return

        if not os.path.exists(source_dir):
            collaborators.printer().print_fn(f"Warning: Source directory not found. path: {source_dir}")
            return

        collaborators.printer().print_fn("Copying configuration files to boot partition...")

        # Copy all files from source directory to boot partition
        # - cmdline.txt
        # - config.txt
        # - firstrun.sh - this script enables SSH on first boot and sets up the required configuration
        # - issue.txt
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            target_item = os.path.join(boot_path, item)

            if os.path.isfile(source_item):
                collaborators.process().run_fn(args=["sudo", "cp", source_item, target_item])
                collaborators.printer().print_fn(f"Copied {item} to boot partition")

        # Clean up any macOS metadata files
        collaborators.printer().print_fn("Cleaning up macOS metadata files...")
        collaborators.process().run_fn(
            allow_single_shell_command_str=True,
            args=[f"sudo find {boot_path} -name '._*' -type f -print -delete 2>/dev/null || true"],
        )

        collaborators.printer().print_fn("SSH access configured with user: pi")
        collaborators.printer().print_fn("First time boot password set to: provisioner")

    def _find_raspberry_pi_boot_partition(self, collaborators: CoreCollaborators) -> str:
        """
        Locate the Raspberry Pi boot partition by checking common mount points.

        Returns:
            str: Path to the boot partition or None if not found
        """
        # Check both possible boot volume paths on MacOS and Linux
        possible_boot_paths = ["/Volumes/bootfs", "/Volumes/boot"]
        boot_path = None

        # First, check if any path exists and contains issue.txt with "Raspberry Pi"
        for path in possible_boot_paths:
            if not os.path.exists(path):
                continue

            issue_file = os.path.join(path, "issue.txt")
            if os.path.exists(issue_file):
                with open(issue_file, "r") as f:
                    if "Raspberry Pi" in f.read():
                        boot_path = path
                        break

        # If no path with issue.txt found, use bootfs if it exists, otherwise boot
        if not boot_path:
            if os.path.exists("/Volumes/bootfs"):
                boot_path = "/Volumes/bootfs"
            elif os.path.exists("/Volumes/boot"):
                boot_path = "/Volumes/boot"

        if boot_path:
            collaborators.printer().print_fn(f"Found boot partition at {boot_path}")
        else:
            collaborators.printer().print_fn("Warning: Boot partition not found")

        return boot_path

    def _extract_image_file(self, image_file_path: str, collaborators: CoreCollaborators) -> tuple[str, str]:
        """
        Extract or decompress image file based on its extension.

        Args:
            image_file_path: Path to the compressed/archived image file
            collaborators: CoreCollaborators instance

        Returns:
            tuple: (extracted_file_path, temp_dir) where:
                - extracted_file_path is the path to the extracted/decompressed file
                - temp_dir is the path to temporary directory (or None if no extraction needed)
        """
        collaborators.printer().print_fn("Checking image file type...")
        file_ext = os.path.splitext(image_file_path)[1].lower()

        # If it's already an image file, just use it directly
        if file_ext in [".img", ".iso", ".raw"]:
            return image_file_path, None

        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        extracted_file_path = ""

        try:
            if file_ext == ".zip":
                collaborators.printer().print_fn("Extracting ZIP file...")
                with zipfile.ZipFile(image_file_path, "r") as zip_ref:
                    # Get list of all files in the archive
                    files = zip_ref.namelist()

                    # Look for image files in the archive
                    image_files = [f for f in files if any(f.lower().endswith(ext) for ext in [".img", ".iso", ".raw"])]

                    if image_files:
                        # Extract the first image file found
                        file_to_extract = image_files[0]
                        collaborators.printer().print_fn(f"Found image file in archive: {file_to_extract}")
                        extracted_file_path = os.path.join(temp_dir, file_to_extract)
                        zip_ref.extract(file_to_extract, temp_dir)
                    else:
                        error_msg = "No image files found in the ZIP archive"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

            elif file_ext == ".gz":
                collaborators.printer().print_fn("Extracting GZIP file...")
                base_name = os.path.basename(image_file_path)
                # If it's a .tar.gz file, handle differently
                if base_name.endswith(".tar.gz"):
                    import tarfile

                    collaborators.printer().print_fn("Detected .tar.gz file, extracting archive...")
                    with tarfile.open(image_file_path, "r:gz") as tar:
                        # Look for image files in the tar archive
                        image_files = [
                            f
                            for f in tar.getnames()
                            if any(f.lower().endswith(ext) for ext in [".img", ".iso", ".raw"])
                        ]
                        if image_files:
                            # Extract the first image file found
                            tar.extract(image_files[0], path=temp_dir)
                            extracted_file_path = os.path.join(temp_dir, image_files[0])
                        else:
                            error_msg = "No image files found in the TAR.GZ archive"
                            logger.error(error_msg)
                            raise ValueError(error_msg)
                else:
                    # Regular .gz file
                    extracted_file_path = os.path.join(temp_dir, base_name[:-3])  # Remove .gz
                    with gzip.open(image_file_path, "rb") as f_in:
                        with open(extracted_file_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

            elif file_ext == ".xz":
                collaborators.printer().print_fn("Extracting XZ file...")
                base_name = os.path.basename(image_file_path)
                # If it's a .tar.xz file, handle differently
                if base_name.endswith(".tar.xz"):
                    import tarfile

                    collaborators.printer().print_fn("Detected .tar.xz file, extracting archive...")
                    with tarfile.open(image_file_path, "r:xz") as tar:
                        # Look for image files in the tar archive
                        image_files = [
                            f
                            for f in tar.getnames()
                            if any(f.lower().endswith(ext) for ext in [".img", ".iso", ".raw"])
                        ]
                        if image_files:
                            # Extract the first image file found
                            tar.extract(image_files[0], path=temp_dir)
                            extracted_file_path = os.path.join(temp_dir, image_files[0])
                        else:
                            error_msg = "No image files found in the TAR.XZ archive"
                            logger.error(error_msg)
                            raise ValueError(error_msg)
                else:
                    # Regular .xz file
                    extracted_file_path = os.path.join(temp_dir, base_name[:-3])  # Remove .xz
                    with lzma.open(image_file_path, "rb") as f_in:
                        with open(extracted_file_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

            else:
                error_msg = f"Unsupported file format: {file_ext}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            return extracted_file_path, temp_dir

        except Exception as e:
            # Clean up temporary directory in case of any errors
            collaborators.io_utils().delete_directory_fn(temp_dir)
            raise e

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
