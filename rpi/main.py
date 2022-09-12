#!/usr/bin/env python3

import typer
from external.python_scripts_lib.cli.entrypoint import main_runner

from rpi.os.cli import os_cli_app

app = typer.Typer(callback=main_runner)
app.add_typer(os_cli_app, name="os")
