#!/usr/bin/env python3

import os
import pathlib

from provisioner_shared.components.runtime.infra.test_context import TestingContext

from provisioner_shared.components.runtime.cli.arg_reader import get_cli_argument_value, is_cli_argument_present
from loguru import logger

from provisioner_shared.components.runtime.cli.entrypoint import EntryPoint
from provisioner_shared.components.runtime.cli.version import append_version_cmd_to_cli
from provisioner_shared.components.runtime.command.config.cli import CONFIG_USER_PATH, append_config_cmd_to_cli
from provisioner_shared.components.runtime.command.plugins.cli import append_plugins_cmd_to_cli
from provisioner_shared.components.runtime.config.domain.config import ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

RUNTIME_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{RUNTIME_ROOT_PATH}/resources/config.yaml"

ENV_VAR_TESTING_MODE_ENABLED = "PROVISIONER_TESTING_MODE_ENABLED"
test_mode = os.getenv(key=ENV_VAR_TESTING_MODE_ENABLED, default=False)

pre_click_ctx = Context.create_empty()
if test_mode:
    pre_click_ctx = TestingContext.create()

# """
# The --dry-run and --verbose flags aren't available on the pre-init phase
# since logger is being set-up after Click is initialized.
# I've added pre Click run env var to control the visiblity of components debug logs
# such as config-loader, package-loader etc..
# """
debug_pre_init = is_cli_argument_present("--verbose", "-v")
pre_click_ctx._verbose = debug_pre_init
if not debug_pre_init:
    logger.remove()

maybe_pkg_mgr = get_cli_argument_value("--package-manager")
if maybe_pkg_mgr:
    pre_click_ctx._pkg_mgr = maybe_pkg_mgr

root_menu = EntryPoint.create_cli_menu()

ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig),
cols = CoreCollaborators(pre_click_ctx)

append_version_cmd_to_cli(root_menu, root_package=RUNTIME_ROOT_PATH)
append_config_cmd_to_cli(root_menu, collaborators=cols)
append_plugins_cmd_to_cli(root_menu, collaborators=cols)

def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(root_menu)

cols.package_loader().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner-runtime", "provisioner_runtime", "provisioner_shared", "provisioner-shared"],
    callback=lambda module: load_plugin(plugin_module=module),
    debug=debug_pre_init,
)

# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    root_menu()
