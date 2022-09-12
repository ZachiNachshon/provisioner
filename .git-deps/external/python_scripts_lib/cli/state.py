#!/usr/bin/env python3

from typing import Optional
from loguru import logger
from ..errors.cli_errors import CliGlobalArgsNotInitialized


class CliGlobalArgs:
    verbose: bool = None
    dry_run: bool = None
    auto_prompt: bool = None

    def __init__(self, verbose: bool, dry_run: bool, auto_prompt: bool) -> None:
        self.verbose = verbose
        self.dry_run = dry_run
        self.auto_prompt = auto_prompt

    @staticmethod
    def create(
        verbose: Optional[bool] = False, 
        dry_run: Optional[bool] = False, 
        auto_prompt: Optional[bool] = False) -> None:
        
        try:
            global cli_global_args
            cli_global_args = CliGlobalArgs(verbose, dry_run, auto_prompt)
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI global args object. ex: {}, message: {}", e_name, str(e))

    @staticmethod
    def is_verbose():
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (main.py)")
        return cli_global_args.verbose

    @staticmethod
    def is_dry_run():
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (main.py)")
        return cli_global_args.dry_run

    @staticmethod
    def is_auto_prompt():
        if not cli_global_args:
            raise CliGlobalArgsNotInitialized("Global args state was not set (main.py)")
        return cli_global_args.auto_prompt

cli_global_args: CliGlobalArgs = None