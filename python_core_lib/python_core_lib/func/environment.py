#!/usr/bin/env python3

from python_core_lib.infra.context import Context


class PyFnEnvBase:
    ctx: Context

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
