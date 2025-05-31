#!/usr/bin/env python3

import click

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup


class EntryPoint:
    @staticmethod
    def create_cli_menu() -> click.Group:
        @click.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
        @cli_modifiers
        @click.pass_context
        def root_menu(ctx: click.Context):
            if ctx.invoked_subcommand is None:
                click.echo(ctx.get_help())

        return root_menu
