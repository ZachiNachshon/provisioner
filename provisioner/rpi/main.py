#!/usr/bin/env python3

import typer

from provisioner.external.python_scripts_lib.python_scripts_lib.cli.entrypoint import main_runner
from provisioner.rpi.os.cli import os_cli_app

app = typer.Typer(no_args_is_help=True, callback=main_runner)
app.add_typer(os_cli_app, name="os")

def main():
    app()