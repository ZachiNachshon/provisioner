#!/usr/bin/env python3

import traceback
from typing import Any, Callable

from loguru import logger

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from python_core_lib.infra.context import Context


class Evaluator:
    @staticmethod
    def eval_step_no_return_throw_on_failure(ctx: Context, err_msg: str, call: Callable) -> None:
        try:
            call()
        except Exception as e:
            raise StepEvaluationFailure(f"{err_msg}, ex: {e.__class__.__name__}, message: {str(e)}")

    @staticmethod
    def eval_step_return_value_throw_on_failure(ctx: Context, err_msg: str, call: Callable) -> Any:
        step_response = call()
        if not step_response and not ctx.is_dry_run():
            raise StepEvaluationFailure(err_msg)
        return step_response

    @staticmethod
    def eval_size_else_throws(ctx: Context, err_msg: str, call: Callable) -> Any:
        step_response = call()
        if not step_response and len(step_response) == 0 and not ctx.is_dry_run():
            raise StepEvaluationFailure(err_msg)
        return step_response

    @staticmethod
    def eval_cli_entrypoint_step(name: str, call: Callable, error_message: str) -> None:
        try:
            call()
        except StepEvaluationFailure as sef:
            # logger.critical(f"{error_message}. name: {name}, ex: {sef.__class__.__name__}, message: {str(sef)}")
            print(str(sef))
        except Exception as e:
            logger.critical(f"{error_message}. name: {name}, ex: {e.__class__.__name__}, message: {str(e)}")
            if CliGlobalArgs.is_verbose():
                raise CliApplicationException(e)

    @staticmethod
    def eval_installer_cli_entrypoint_pyfn_step(name: str, call: Callable) -> None:
        is_failure = False
        raised: Exception = None
        should_re_raise = False
        response = None
        try:
            response = call()
        except StepEvaluationFailure as sef:
            # is_failure = True
            # raised = sef
            print(str(sef))
        except Exception as ex:
            if CliGlobalArgs.is_verbose():
                traceback.print_exc()
            is_failure = True
            raised = ex
            should_re_raise = True

        if CliGlobalArgs.is_verbose() and (is_failure or not response):
            logger.critical(
                f"Failed to install CLI utility. name: {name}, ex: {raised.__class__.__name__}, message: {str(raised)}"
            )
            if should_re_raise and CliGlobalArgs.is_verbose():
                raise CliApplicationException(raised)
