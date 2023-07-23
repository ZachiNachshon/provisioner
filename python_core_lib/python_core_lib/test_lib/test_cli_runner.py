#!/usr/bin/env python3

from typing import Any, Callable

from typer.testing import CliRunner


class TestCliRunner:
    def run(callable: Callable[[CliRunner], Any]) -> Any:
        result = callable(CliRunner())
        if result.exit_code != 0:
            return result
        else:
            return result.stdout
