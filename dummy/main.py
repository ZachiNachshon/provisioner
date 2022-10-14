#!/usr/bin/env python3

import typer
from external.python_scripts_lib.python_scripts_lib.cli.entrypoint import main_runner

from dummy.hello_world.cli import dummy_cli_app

app = typer.Typer(callback=main_runner)
app.add_typer(dummy_cli_app, name="hello_world")
