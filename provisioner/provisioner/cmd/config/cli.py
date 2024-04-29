#!/usr/bin/env python3

import copy
import json
import os
from typing import Any, Optional
from loguru import logger
from provisioner.colors import colors
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

def flush_config(
    force: Optional[bool] = typer.Option(
    None, show_default=True, help="Force flush and delete config file if exist", envvar="PROV_FORCE_FLUSH_CONFIG"
    )
) -> None:
    
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH) and not force:
        collaboratos.printer().print_fn("User configuration file already exists. Use --force to overwrite.")
        return

    cfg_yaml = _get_user_facing_config_yaml()
    collaboratos.io_utils().write_file_fn(
        content=cfg_yaml, 
        file_name=os.path.basename(CONFIG_USER_PATH), 
        dir_path=os.path.dirname(CONFIG_USER_PATH))
    
    collaboratos.printer().print_fn(f"Internal configuration flushed to user configuration file. path: {CONFIG_USER_PATH}")
    collaboratos.printer().print_with_rich_table_fn(cfg_yaml)

def view_config() -> None:
    cfg_yaml = _get_user_facing_config_yaml()
    collaboratos.printer().print_with_rich_table_fn(cfg_yaml)
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.printer().print_fn(colors.color_text(f"Identified user overrides. path: {CONFIG_USER_PATH}", colors.YELLOW))

def _get_user_facing_config_yaml() -> str:
    cfg_dict_obj = ConfigManager.instance().get_config().dict_obj
    # Create a deep copy of the dictionary, not to tamper with the original object
    copied_cfg_dict_obj = copy.deepcopy(cfg_dict_obj)
    user_facing_cfg = _remove_cfg_internal_attributes(copied_cfg_dict_obj)
    cfg_json = json.dumps(user_facing_cfg, default=lambda o: o.__dict__, indent=4)
    return collaboratos.yaml_util().json_to_yaml_fn(cfg_json)

def _remove_cfg_internal_attributes(cfg_dict_obj: dict) -> Any:
    # Remove 'plugins_definitions' attribute
    if "plugins_definitions" in cfg_dict_obj:
        del cfg_dict_obj["plugins_definitions"]

    # Recursively remove all 'dict_obj' variables
    remove_key(cfg_dict_obj, "dict_obj")

    # Return the modified data
    return cfg_dict_obj

def remove_key(data, key):
    if isinstance(data, dict):
        if key in data:
            del data[key]
        for value in data.values():
            remove_key(value, key)
    elif isinstance(data, list):
        for item in data:
            remove_key(item, key)
    else:
        return remove_attribute_from_obj(data, key)
    
def remove_attribute_from_obj(obj, attr):
    if hasattr(obj, attr):
        delattr(obj, attr)
    for attribute in dir(obj):
        if attribute.startswith('__') and attribute.endswith('__'):
            # Ignore Python internal attributes/methods
            continue
        attr_value = getattr(obj, attribute)
        if isinstance(attr_value, list):
            for item in attr_value:
                remove_attribute_from_obj(item, attr)
        elif isinstance(attr_value, dict):
            for item in attr_value.values():
                remove_attribute_from_obj(item, attr)
        else:
            remove_attribute_from_obj(attr_value, attr)
        