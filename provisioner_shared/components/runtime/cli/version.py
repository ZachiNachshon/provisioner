#!/usr/bin/env python3


import click
from loguru import logger


def append_version_cmd_to_cli(root_menu: click.Group, root_package: str, description: str = "Print runtime version"):
    @root_menu.command(help=description)
    @click.pass_context
    def version(ctx):
        print(try_read_version(root_package))
        ctx.exit(0)


def try_read_version(root_package: str) -> str:
    content = "no version"
    try:
        # file_path = Paths.create(Context.create()).get_file_path_from_python_package(
        #     root_package, "version.txt"
        # )
        file_path = f"{root_package }/resources/version.txt"
        with open(file_path, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception as ex:
        logger.error(f"Failed to read version file. ex: {ex}")
        pass
    return content
