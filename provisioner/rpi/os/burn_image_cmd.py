#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from provisioner.common.sd_card.image_burner import (
    ImageBurnerArgs,
    ImageBurnerCmdRunner,
    ImageBurnerCollaborators,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context


class RPiOsBurnImageCmdArgs:

    image_download_url: str
    image_download_path: str

    def __init__(self, image_download_url: Optional[str] = None, image_download_path: Optional[str] = None) -> None:

        self.image_download_url = image_download_url
        self.image_download_path = image_download_path

    def print(self) -> None:
        logger.debug(
            "RPiOsBurnImageCmdArgs: \n"
            + f"  image_download_url: {self.image_download_url}\n"
            + f"  image_download_path: {self.image_download_path}\n"
        )


class RPiOsBurnImageCmd:
    def run(self, ctx: Context, args: RPiOsBurnImageCmdArgs) -> None:
        logger.debug("Inside RPiOsBurnImageCmd run()")

        ImageBurnerCmdRunner().run(
            ctx=ctx,
            args=ImageBurnerArgs(download_url=args.image_download_url, download_path=args.image_download_path),
            collaborators=ImageBurnerCollaborators(ctx),
        )
