#!/usr/bin/env python3


import click
from loguru import logger

from components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.paths import Paths

STATIC_RESOURCES_PACKAGE = "provisioner.resources"

def append_version_cmd_to_cli(root_menu: click.Group, cols: CoreCollaborators):
  
  @root_menu.command()
  @click.pass_context
  def version(ctx):
    """Print client version"""
    print(try_read_version())
    ctx.exit(0)

def try_read_version() -> str:
    content = "no version"
    try:
        file_path = Paths.create(Context.create()).get_file_path_from_python_package(
            STATIC_RESOURCES_PACKAGE, "version.txt"
        )
        with open(file_path, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception as ex:
        logger.error(f"Failed to read version file. ex: {ex}")
        pass
    return content