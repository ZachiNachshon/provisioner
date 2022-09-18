#!/usr/bin/env python3

from typing import Optional
from loguru import logger
from common.sd_card.image_burner import ImageBurnerCollaborators, ImageBurnerRunner, ImageBurnerArgs
from external.python_scripts_lib.python_scripts_lib.utils.properties import Properties
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.infra.context import Context

PROPERTIES_FILE_PATH = "rpi/os/config.properties"


class RPiOsConfigureArgs:

    image_download_url: str

    def __init__(self, image_download_url: Optional[str] = None) -> None:
        self.image_download_url = image_download_url

    def print(self) -> None:
        logger.debug("RPiOsConfigureArgs: \n" "  image_download_url: {}".format(self.image_download_url))


class Collaborators:
    properties = Properties


class RPiOsConfigureCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils()
        self.properties = Properties.create(self.io)


class RPiOsConfigureRunner:
    def _read_property(self, properties: Properties, key: str) -> str:
        return properties.read_value_fn(PROPERTIES_FILE_PATH, key)

    def _get_os_raspbian_download_url(
        self,
        properties: Properties,
    ) -> str:
        os_system = self._read_property(properties, "rpi.os.raspbian.os.system")
        # 32 / 64 bit systems
        os_raspbian_download_url = self._read_property(
            properties, "rpi.os.raspbian.{}.bit.download.url".format(os_system)
        )
        return os_raspbian_download_url

    def run(self, ctx: Context, args: RPiOsConfigureArgs, collaborators: Collaborators) -> None:
        logger.debug("Inside RpiOsConfigureRunner run()")

        image_download_url = args.image_download_url
        if args.image_download_url is None:
            image_download_url = self._get_os_raspbian_download_url(collaborators.properties)

        ImageBurnerRunner().run(
            ctx=ctx, args=ImageBurnerArgs(image_download_url), collaborators=ImageBurnerCollaborators(ctx)
        )
