#!/usr/bin/env python3

from provisioner.infra.context import Context


class PyFnEnvBase:
    ctx: Context

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
