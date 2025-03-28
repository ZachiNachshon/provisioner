#!/usr/bin/env python3

import copy
import json
import os
from typing import Any, Optional

import click
from loguru import logger

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.colors import colors
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")


def append_config_cmd_to_cli(root_menu: click.Group, collaborators: CoreCollaborators):

    @root_menu.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def config(ctx):
        """Configuration management"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @config.command()
    def clear():
        """Clear local config file, rely on internal configuration only"""
        clear_config(collaborators)

    @config.command()
    @cli_modifiers
    def edit():
        """Edit user configuration file"""
        edit_config(collaborators)

    @config.command()
    @cli_modifiers
    @click.option(
        "--force",
        is_flag=True,
        help="Force flush and delete config file if exist",
        envvar="PROV_FORCE_FLUSH_CONFIG",
    )
    @cli_modifiers
    def flush(force: bool):
        """Flush internal configuration to a user config file"""
        flush_config(force, collaborators)

    @config.command()
    @cli_modifiers
    def view():
        """Print configuration to stdout"""
        view_config(collaborators)


def clear_config(collaboratos: CoreCollaborators) -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.io_utils().delete_file_fn(CONFIG_USER_PATH)
        logger.info(f"Local configuration cleared successfully. path: {CONFIG_USER_PATH}")
    else:
        logger.info(f"No local user configuration file, nothing to remove. path: {CONFIG_USER_PATH}")


def edit_config(collaboratos: CoreCollaborators) -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.editor().open_file_for_edit_fn(CONFIG_USER_PATH)
    else:
        logger.info(f"No local user configuration file. path: {CONFIG_USER_PATH}")


def flush_config(force: Optional[bool], collaboratos: CoreCollaborators) -> None:
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH) and not force:
        collaboratos.printer().print_fn("User configuration file already exists. Use --force to overwrite.")
        return

    cfg_yaml = _get_user_facing_config_yaml(collaboratos)
    collaboratos.io_utils().write_file_fn(
        content=cfg_yaml, file_name=os.path.basename(CONFIG_USER_PATH), dir_path=os.path.dirname(CONFIG_USER_PATH)
    )

    collaboratos.printer().print_fn(
        f"Internal configuration flushed to user configuration file. path: {CONFIG_USER_PATH}"
    )
    collaboratos.printer().print_with_rich_table_fn(cfg_yaml)


def view_config(collaboratos: CoreCollaborators) -> None:
    cfg_yaml = _get_user_facing_config_yaml(collaboratos)
    collaboratos.printer().print_with_rich_table_fn(cfg_yaml)
    if collaboratos.io_utils().file_exists_fn(CONFIG_USER_PATH):
        collaboratos.printer().print_fn(
            colors.color_text(f"Identified user overrides. path: {CONFIG_USER_PATH}", colors.YELLOW)
        )


def _get_user_facing_config_yaml(collaboratos: CoreCollaborators) -> str:
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


def remove_attribute_from_obj(obj, attr, depth=0, max_depth=10):
    """Remove an attribute from an object and its nested structures.

    Args:
        obj: The object to process
        attr: The attribute name to remove
        depth: Current recursion depth
        max_depth: Maximum allowed recursion depth
    """
    if depth >= max_depth:
        return

    # Handle None and primitive types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return

    # Handle the object itself
    if hasattr(obj, attr):
        delattr(obj, attr)

    # Handle different types of objects
    if isinstance(obj, (list, tuple)):
        for item in obj:
            remove_attribute_from_obj(item, attr, depth + 1, max_depth)
    elif isinstance(obj, dict):
        for value in obj.values():
            remove_attribute_from_obj(value, attr, depth + 1, max_depth)
    elif hasattr(obj, "__dict__"):
        # Only process object attributes if it's a custom object
        for attribute in dir(obj):
            if attribute.startswith("__") and attribute.endswith("__"):
                continue
            try:
                attr_value = getattr(obj, attribute)
                remove_attribute_from_obj(attr_value, attr, depth + 1, max_depth)
            except (AttributeError, TypeError):
                continue
