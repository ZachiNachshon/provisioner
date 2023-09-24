#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import NotInitialized
from python_core_lib.utils.os import OsArch

cli_context = None


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


class CliContextManager:
    @staticmethod
    def create():
        os_arch_str = CliGlobalArgs.maybe_get_os_arch_flag_value()
        os_arch = OsArch.from_string(os_arch_str) if os_arch_str else None

        return Context.create(
            dry_run=CliGlobalArgs.is_dry_run(),
            verbose=CliGlobalArgs.is_verbose(),
            auto_prompt=CliGlobalArgs.is_auto_prompt(),
            os_arch=os_arch,
        )
