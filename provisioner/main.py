#!/usr/bin/env python3

import os
import pathlib

from components.runtime.cli.entrypoint import EntryPoint
from loguru import logger

from provisioner_shared.components.runtime.cli.version import append_version_cmd_to_cli
from provisioner_shared.components.runtime.command.config.cli import CONFIG_USER_PATH, append_config_cmd_to_cli
from provisioner_shared.components.runtime.command.plugins.cli import append_plugins_cmd_to_cli
from provisioner_shared.components.runtime.config.domain.config import ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

RUNTIME_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{RUNTIME_ROOT_PATH}/resources/config.yaml"

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


root_menu = EntryPoint.create_cli_menu()

ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig),


def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(root_menu)


cols = CoreCollaborators(Context.create_empty())
cols.package_loader().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner-runtime", "provisioner_runtime", "provisioner_shared", "provisioner-shared"],
    callback=lambda module: load_plugin(plugin_module=module),
    debug=debug_pre_init,
)

append_version_cmd_to_cli(root_menu, root_package=RUNTIME_ROOT_PATH)
append_config_cmd_to_cli(root_menu, collaborators=cols)
append_plugins_cmd_to_cli(root_menu, collaborators=cols)


# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    root_menu()
