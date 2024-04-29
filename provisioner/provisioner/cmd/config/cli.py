#!/usr/bin/env python3

import json
import os
from typing import Any
from loguru import logger
from provisioner.config.manager.config_manager import ConfigManager
from provisioner.shared.collaborators import CoreCollaborators
import typer

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")

collaboratos: CoreCollaborators = None

def append_config_cmd_to_cli(app: typer.Typer, cli_group_name: str, cols: CoreCollaborators):
    global collaboratos
    collaboratos = cols

    # Create the CLI structure
    config_cli_app = typer.Typer()
    app.add_typer(
        config_cli_app,
        name="config",
        invoke_without_command=True,
        no_args_is_help=True,
        # rich_help_panel=cli_group_name,
        help="Configuration management",
    )

    clear_config_cli_app = typer.Typer()
    config_cli_app.add_typer(
        clear_config_cli_app,
        name="clear",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=clear_config,
        help="Clear local config file, rely on internal configuration only",
    )

    edit_config_cli_app = typer.Typer()
    config_cli_app.add_typer(
        edit_config_cli_app,
        name="edit",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=edit_config,
        help="Edit user configuration file",
    )

    flush_config_cli_app = typer.Typer()
    config_cli_app.add_typer(
        flush_config_cli_app,
        name="flush",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=flush_config,
        help="Flush internal configuration to a user config file",
    )

    view_config_cli_app = typer.Typer()
    config_cli_app.add_typer(
        view_config_cli_app,
        name="view",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=view_config,
        help="Print configuration to stdout",
    )

def clear_config() -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.io_utils().delete_file_fn(CONFIG_USER_PATH)
    else:
        logger.info(f"No local user configuration file, nothing to remove. path: {CONFIG_USER_PATH}")

def edit_config() -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.editor().open_file_for_edit_fn(CONFIG_USER_PATH)
    else:
        logger.info(f"No local user configuration file. path: {CONFIG_USER_PATH}")

def flush_config() -> None:
    print("Flush configuration")
    cfg_dict_obj = ConfigManager.instance().get_config().dict_obj
    prov_cfg_no_parent = cfg_dict_obj["provisioner"]
    cfg_json = json.dumps(prov_cfg_no_parent, default=lambda o: o.__dict__, indent=4)
    print(cfg_json)

def view_config() -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        content = collaboratos.io_utils().read_file_safe_fn(CONFIG_USER_PATH)
        collaboratos.printer().print_fn(content)
    else:
        logger.info(f"No local user configuration file. path: {CONFIG_USER_PATH}")

