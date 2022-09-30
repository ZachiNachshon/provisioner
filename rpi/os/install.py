#!/usr/bin/env python3

import os
from typing import Optional
from loguru import logger
from rpi.os.domain.config import ProvisionerConfig
from common.sd_card.image_burner import ImageBurnerCollaborators, ImageBurnerRunner, ImageBurnerArgs
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.config.config_reader import ConfigReader
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "rpi/config.yaml"


class RPiOsInstallArgs:

    image_download_url: str

    def __init__(self, image_download_url: Optional[str] = None) -> None:
        self.image_download_url = image_download_url

    def print(self) -> None:
        logger.debug("RpiOsInstallArgs: \n" +
            f"  image_download_url: {self.image_download_url}")


class Collaborators:
    config_reader = ConfigReader


class RPiOsInstallCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.yaml_util = YamlUtil.create(ctx, self.io)
        self.config_reader = ConfigReader.create(self.yaml_util)


class RPiOsInstallRunner:
    def run(self, ctx: Context, args: RPiOsInstallArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RpiOsInstallRunner run()")

        config: ProvisionerConfig = collaborators.config_reader.read_config_fn(
            internal_path=CONFIG_INTERNAL_PATH, 
            class_name=ProvisionerConfig,
            user_path=CONFIG_USER_PATH)

        image_download_url = config.get_os_raspbian_download_url() if args.image_download_url is None else args.image_download_url
        image_download_path = config.download_path

        ImageBurnerRunner().run(
            ctx=ctx, 
            args=ImageBurnerArgs(image_download_url, image_download_path), 
            collaborators=ImageBurnerCollaborators(ctx)
        )
