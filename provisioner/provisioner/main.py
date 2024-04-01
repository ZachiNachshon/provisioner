#!/usr/bin/env python3

import os
import pathlib

from loguru import logger

from provisioner.cli.entrypoint import EntryPoint
from provisioner.config.domain.config import ProvisionerConfig
from provisioner.config.manager.config_manager import ConfigManager
from provisioner.utils.package_loader import PackageLoader

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/resources/config.yaml"

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

if not debug_pre_init:
    logger.remove()

app = EntryPoint.create_typer(
    title="Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)",
    config_resolver_fn=lambda: ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig),
)


def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(app)


PackageLoader.create().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner", "provisioner-features-lib"],
    callback=lambda module: load_plugin(plugin_module=module),
    debug=debug_pre_init,
)

# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    app()
