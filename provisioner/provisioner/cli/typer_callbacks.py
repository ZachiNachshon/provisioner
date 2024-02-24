#!/usr/bin/env python3

from typing import List, Optional

import typer


def MutuallyExclusiveGroup():
    """
    Enforce mutual exclusivity on two CLI options.
    Limit to x2 options, we want to keep CLI usage simple
    If there are more than x2 mutual exclusive options, maybe a sub-command should be used
    Usage:
    option_1: str = typer.Option(
        None,
        help="Option 1 description",
        callback=exclusivity_callback,
    ),
    option_2: str = typer.Option(
        None,
        help="Option 2 description",
        callback=exclusivity_callback,
    ),
    """
    group = set()

    def callback(ctx: typer.Context, param: typer.CallbackParam, value: str):
        # Add cli option to group if it was called with a value
        if value is not None and len(value) > 0 and len(group) == 0:
            group.add(param.name)
        if value is not None and len(value) > 0 and param.name not in group:
            raise typer.BadParameter(f"{param.name} is mutually exclusive with {group.pop()}")
        return value

    return callback


exclusivity_callback = MutuallyExclusiveGroup()


def collect_typer_options_into_list(typer_options) -> Optional[List[str]]:
    result: Optional[List[str]] = None
    if typer_options and typer_options is not None:
        result = []
        for opt in typer_options:
            result.append(opt.strip())
    return result
