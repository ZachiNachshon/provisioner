#!/usr/bin/env python3

import json

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
        #     root_package, "manifest.json"
        # )
        file_path = f"{root_package}/resources/manifest.json"
        with open(file_path, "r") as opened_file:
            manifest = json.load(opened_file)

            # For runtime manifests, use 'version' instead of 'plugin_version'
            # For plugin manifests, still support 'plugin_version' for backward compatibility
            version = manifest.get("version") or manifest.get("plugin_version")
            if version:
                content = version
            else:
                logger.warning(f"No version field found in manifest: {file_path}")

    except FileNotFoundError:
        logger.error(f"Manifest file not found: {file_path}")
    except json.JSONDecodeError as ex:
        logger.error(f"Invalid JSON in manifest file {file_path}. ex: {ex}")
    except Exception as ex:
        logger.error(f"Failed to read manifest file. ex: {ex}")

    return content
