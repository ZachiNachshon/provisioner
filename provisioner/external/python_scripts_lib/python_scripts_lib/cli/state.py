#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from ..errors.cli_errors import CliGlobalArgsNotInitialized


class CliGlobalArgs:
    verbose: bool
    dry_run: bool
    auto_prompt: bool
    os_arch: str

    def __init__(self, verbose: bool, dry_run: bool, auto_prompt: bool, os_arch: str) -> None:

        self.verbose = verbose
        self.dry_run = dry_run
        self.auto_prompt = auto_prompt
        self.os_arch = os_arch

    @staticmethod
    def create(
        verbose: Optional[bool] = False,
        dry_run: Optional[bool] = False,
        auto_prompt: Optional[bool] = False,
        os_arch: Optional[str] = None,
    ) -> None:

        try:
            global cli_global_args
            cli_global_args = CliGlobalArgs(verbose, dry_run, auto_prompt, os_arch)
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI global args object. ex: {}, message: {}", e_name, str(e))

    @staticmethod
    def is_verbose() -> bool:
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (entrypoint.py)")
        return cli_global_args.verbose

    @staticmethod
    def is_dry_run() -> bool:
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (entrypoint.py)")
        return cli_global_args.dry_run

    @staticmethod
    def is_auto_prompt() -> bool:
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (entrypoint.py)")
        return cli_global_args.auto_prompt

    @staticmethod
    def maybe_get_os_arch_flag_value() -> str:
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (entrypoint.py)")
        return cli_global_args.os_arch


cli_global_args: CliGlobalArgs = None
