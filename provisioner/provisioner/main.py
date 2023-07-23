#!/usr/bin/env python3

import os
import pathlib

from provisioner_features_lib.config.config_resolver import ConfigResolver
from python_core_lib.cli.entrypoint import EntryPoint
from python_core_lib.utils.package_loader import PackageLoader

from provisioner.config.domain.config import ProvisionerConfig

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/config/config.yaml"

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to contorl if such components debug logs
should be visible (config-loader, package-loader etc..)
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

app = EntryPoint.create_typer(
    title="Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)",
    config_resolver_fn=lambda: ConfigResolver.load(
        CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, class_name=ProvisionerConfig, debug=debug_pre_init
    ),
)

PackageLoader.create().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner", "provisioner-features-lib"],
    callback=lambda module: module.append_to_cli(app),
    debug=debug_pre_init,
)

# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    app()
