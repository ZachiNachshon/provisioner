#!/usr/bin/env python3

import os
import pathlib

from loguru import logger

from provisioner_shared.components.runtime.cli.entrypoint import EntryPoint
from provisioner_shared.components.runtime.command.config.cli import CONFIG_USER_PATH, append_config_cmd_to_cli
from provisioner_shared.components.runtime.command.plugins.cli import append_plugins_cmd_to_cli
from provisioner_shared.components.runtime.config.domain.config import ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/resources/config.yaml"

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Click is initialized.
I've added pre Click run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

if not debug_pre_init:
    logger.remove()

ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig)

root_menu = EntryPoint.create_cli_menu()


def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(root_menu)


# ==============
# ENTRY POINT
# To run from source:
#   - PLUGIN_NAME="provisioner_examples_plugin" poetry run plugin
# ==============
def main():
    # print(f"sys.path: {sys.path}")

    plugin_name = os.getenv("PLUGIN_NAME")
    if not plugin_name:
        raise ValueError("PLUGIN_NAME environment variable is required.")

    logger.debug(f"Loading plugin: {plugin_name}")

    cols = CoreCollaborators(Context.create_empty())
    cols.package_loader().import_modules_fn(
        packages=[f"plugins.{plugin_name}.{plugin_name}"],
        import_path="main",
        callback=lambda module: load_plugin(plugin_module=module),
    )

    append_config_cmd_to_cli(root_menu=root_menu, collaborators=cols)
    append_plugins_cmd_to_cli(root_menu=root_menu, collaborators=cols)

    root_menu()
