#!/usr/bin/env python3

import typer
from external.python_scripts_lib.python_scripts_lib.cli.entrypoint import main_runner

from k3s.master.cli import master_cli_app

app = typer.Typer(callback=main_runner)
app.add_typer(master_cli_app, name="master")
# app.add_typer(agent_cli_app, name="agent")
