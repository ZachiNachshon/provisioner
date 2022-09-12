#!/usr/bin/env python3

from typing import Optional
from loguru import logger

from ..cli.state import CliGlobalArgs
from ..errors.cli_errors import NotInitialized
from ..utils.os import OsArch


class Context:
    os_arch: OsArch
    _verbose: bool = None
    _dry_run: bool = None
    _auto_prompt: bool = None

    @staticmethod
    def create(
        dry_run: Optional[bool] = False,
        verbose: Optional[bool] = False,
        auto_prompt: Optional[bool] = False,
        os_arch: Optional[OsArch] = None,
    ) -> "Context":

        try:
            ctx = Context()
            ctx.os_arch = os_arch if os_arch else OsArch()
            ctx._dry_run = dry_run
            ctx._verbose = verbose
            ctx._auto_prompt = auto_prompt
            return ctx
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create context object. ex: {}, message: {}", e_name, str(e))

    def is_verbose(self) -> bool:
        if self._verbose is None:
            raise NotInitialized("context mandatory variable is not initialized. name: verbose")
        return self._verbose

    def is_dry_run(self) -> bool:
        if self._dry_run is None:
            raise NotInitialized("context mandatory variable is not initialized. name: dry_run")
        return self._dry_run

    def is_auto_prompt(self) -> bool:
        if self._auto_prompt is None:
            raise NotInitialized("context mandatory variable is not initialized. name: auto_prompt")
        return self._auto_prompt
