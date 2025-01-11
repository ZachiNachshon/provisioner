#!/usr/bin/env python3

from typing import Any, Callable, Optional
from provisioner_shared.components.runtime.cli.version import STATIC_RESOURCES_PACKAGE

class EntryPoint:
    @staticmethod
    def create_cli_menu(
        config_resolver_fn: Optional[Callable] = None,
        version_package_path: Optional[str] = STATIC_RESOURCES_PACKAGE,
    ) -> Any:

        if len(version_package_path) > 0:
            global STATIC_RESOURCES_PACKAGE
            STATIC_RESOURCES_PACKAGE = version_package_path

        if config_resolver_fn:
            config_resolver_fn()

        # # Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
        # # Use also no_args_is_help=True to print the help menu if no arguments were supplied
        # return typer.Typer(
        #     # help=title, callback=main_runner, invoke_without_command=True, no_args_is_help=True, rich_markup_mode="rich"
        #     help=title, invoke_without_command=True, no_args_is_help=True, rich_markup_mode="rich"
        # )
