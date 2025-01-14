#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.utils.os import OsArch


class Context:
    os_arch: OsArch
    _verbose: bool = None
    _dry_run: bool = None
    _auto_prompt: bool = None
    _non_interactive: bool = None

    @staticmethod
    def create_empty() -> "Context":
        ctx = Context()
        ctx.os_arch = OsArch()
        ctx._dry_run = False
        ctx._verbose = False
        ctx._auto_prompt = False
        ctx._non_interactive = False
        return ctx

    @staticmethod
    def create(
        dry_run: Optional[bool] = False,
        verbose: Optional[bool] = False,
        auto_prompt: Optional[bool] = False,
        non_interactive: Optional[bool] = False,
        os_arch: Optional[OsArch] = None,
    ) -> "Context":

        try:
            ctx = Context()
            ctx.os_arch = os_arch if os_arch else OsArch()
            ctx._dry_run = dry_run
            ctx._verbose = verbose
            ctx._auto_prompt = auto_prompt
            ctx._non_interactive = non_interactive
            return ctx
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create context object. ex: {}, message: {}", e_name, str(e))

    def is_verbose(self) -> bool:
        return self._verbose

    def is_dry_run(self) -> bool:
        return self._dry_run

    def is_auto_prompt(self) -> bool:
        return self._auto_prompt

    def is_non_interactive(self) -> bool:
        return self._non_interactive


class CliContextManager:

    @staticmethod
    def create(modifiers: CliModifiers) -> Context:
        os_arch_str = modifiers.maybe_get_os_arch_flag_value()
        os_arch = OsArch.from_string(os_arch_str) if os_arch_str else None

        return Context.create(
            dry_run=modifiers.is_dry_run(),
            verbose=modifiers.is_verbose(),
            auto_prompt=modifiers.is_auto_prompt(),
            non_interactive=modifiers.is_non_interactive(),
            os_arch=os_arch,
        )
