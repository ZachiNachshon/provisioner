#!/usr/bin/env python3

from provisioner_shared.components.runtime.infra.context import Context


class PyFnEnvBase:
    ctx: Context

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
