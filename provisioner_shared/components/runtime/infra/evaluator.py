#!/usr/bin/env python3

import traceback
from typing import Any, Callable

import click
from loguru import logger

from provisioner_shared.components.runtime.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from provisioner_shared.components.runtime.infra.context import Context


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
    def eval_cli_entrypoint_step(name: str, call: Callable, error_message: str, verbose: bool = False) -> None:
        try:
            call()
        except StepEvaluationFailure as sef:
            logger.critical(f"{error_message}. name: {name}, ex: {sef.__class__.__name__}, message: {str(sef)}")
            print(str(sef))
        except Exception as e:
            logger.critical(f"{error_message}. name: {name}, ex: {e.__class__.__name__}, message: {str(e)}")
            print("================================")
            print(e.__class__.__name__)
            print("================================")
            if verbose:
                raise CliApplicationException(e)
            raise click.ClickException(error_message)

    @staticmethod
    def eval_installer_cli_entrypoint_pyfn_step(name: str, call: Callable, verbose: bool = False) -> None:
        raised: Exception = None
        is_failure = False
        try:
            call()
        except StepEvaluationFailure as sef:
            is_failure = True
            print(str(sef))
        except Exception as ex:
            is_failure = True
            if verbose:
                traceback.print_exc()
            raised = ex

        if verbose and is_failure:
            logger.critical(
                f"Failed to install CLI utility. name: {name}, ex: {raised.__class__.__name__}, message: {str(raised)}"
            )
            raise CliApplicationException(raised)
        elif is_failure:
            # logger.error(f"name: {name}, exception: {raised.__class__.__name__}, message: {str(raised)}")
            raise click.ClickException(f"name: {name}, exception: {raised.__class__.__name__}, message: {str(raised)}")

        # if verbose and (is_failure or not response):
        #     logger.critical(
        #         f"Failed to install CLI utility. name: {name}, ex: {raised.__class__.__name__}, message: {str(raised)}"
        #     )
        #     if should_re_raise and verbose:
        #         raise CliApplicationException(raised)
