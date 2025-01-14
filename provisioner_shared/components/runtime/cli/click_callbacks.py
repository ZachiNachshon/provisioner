#!/usr/bin/env python3


import click


def mutually_exclusive_group():
    """
    Enforce mutual exclusivity on two CLI options.
    Usage:
        @click.option("--option1", callback=mutually_exclusive_callback)
        @click.option("--option2", callback=mutually_exclusive_callback)
    """
    group = set()

    def callback(ctx, param, value):
        if value is not None:
            # Add the parameter to the group if it's not already there
            if not group:
                group.add(param.name)
            elif param.name not in group:
                raise click.BadParameter(f"{param.name} is mutually exclusive with {group.pop()}")
        return value

    return callback


mutually_exclusive_callback = mutually_exclusive_group()
