#!/usr/bin/env python3

import subprocess
import os
from loguru import logger
from typing import List, Optional
from ..infra.context import Context


class Process:

    _dry_run: bool = None
    _verbose: bool = None

    def __init__(self, dry_run: bool, verbose: bool) -> None:
        self._dry_run = dry_run
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context) -> "Process":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating process executor (dry_run: {dry_run}, verbose: {verbose})...")
        return Process(dry_run, verbose)

    def _run(
        self,
        args: List[str],
        working_dir: Optional[str] = None,
        fail_msg: Optional[str] = "",
        fail_on_error: Optional[bool] = True,
        allow_single_shell_command_str: Optional[bool] = False,
    ) -> str:

        if self._dry_run:
            cmd_str = " ".join(args)
            print(f"\n    {cmd_str}\n")
            return ""

        logger.debug("Running process:\t{}", " ".join(args))

        cwd = working_dir if working_dir else os.getcwd()
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            shell=allow_single_shell_command_str,
        )

        encoded_out, err = process.communicate()
        out = encoded_out.decode("utf-8")
        if process.returncode != 0 and fail_on_error:
            msg = "{}. code= {}, output: {}, stderr: {}".format(fail_msg, process.returncode, out, err)
            logger.error(msg)
            raise Exception(msg)

        # logger.debug("Process output:\n{}", out)
        return out

    def _is_tool_exist(self, name: str) -> bool:
        output = self._run(args=["command -v " + name], fail_on_error=False, allow_single_shell_command_str=True)
        return len(output.strip()) > 0

    run_fn = _run
    is_tool_exist_fn = _is_tool_exist
