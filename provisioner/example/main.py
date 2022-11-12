#!/usr/bin/env python3

import typer

from provisioner.example.dummy.cli import dummy_cli_app
from provisioner.external.python_scripts_lib.python_scripts_lib.cli.entrypoint import main_runner

app = typer.Typer(callback=main_runner)
app.add_typer(dummy_cli_app, name="dummy")
