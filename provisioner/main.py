#!/usr/bin/env python3

import pathlib

from provisioner_shared.components.runtime.cli.arg_reader import PreRunArgs
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

pre_click_ctx = Context.create_empty()
pre_run_args: PreRunArgs = PreRunArgs().handle_pre_click_args(ctx=pre_click_ctx)
cols = CoreCollaborators(pre_click_ctx)

root_menu = EntryPoint.create_cli_menu()
ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig)

append_version_cmd_to_cli(root_menu, root_package=RUNTIME_ROOT_PATH)
append_config_cmd_to_cli(root_menu, collaborators=cols)
append_plugins_cmd_to_cli(root_menu, collaborators=cols)


def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(root_menu)


cols.package_loader().load_modules_with_version_check_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner-runtime", "provisioner-shared"],
    callback=lambda module: load_plugin(plugin_module=module),
    debug=pre_run_args.debug_pre_init,
)


# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    root_menu()
