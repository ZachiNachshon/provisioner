#!/usr/bin/env python3

from typing import Any, Callable

from loguru import logger

from ..errors.cli_errors import StepEvaluationFailure
from .context import Context


class Evaluator:
    @staticmethod
    def eval_step_failure_throws(ctx: Context, err_msg: str, call: Callable) -> Any:
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