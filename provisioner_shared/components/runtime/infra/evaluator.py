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
            if verbose:
                raise CliApplicationException(e)
            raise click.ClickException(error_message)

    @staticmethod
    def eval_installer_cli_entrypoint_pyfn_step(name: str, call: Callable, verbose: bool = False) -> None:
        """Execute a CLI command and handle errors appropriately.

        Args:
            name: Name of the command for error reporting
            call: The callable function to execute
            verbose: Whether to provide detailed error information
        """
        logger.debug(f"Starting CLI step: {name}")

        try:
            # Validate input
            if call is None:
                raise ValueError("Call function cannot be None")

            # Execute the call
            response = call()
            logger.debug(f"Command executed successfully, response: {response}")

            # Success case - return
            return

        except StepEvaluationFailure as sef:
            # Print evaluation failure directly to user
            # print(str(sef))
            error = sef
        except TypeError as te:
            # Special handling for TypeError (common with None values)
            logger.critical(f"TypeError: {str(te)}")
            if "NoneType" in str(te):
                logger.critical("NoneType error detected, likely an unexpected None value")
            error = te
        except Exception as ex:
            # General exception handling
            logger.critical(f"Exception occurred: {ex.__class__.__name__}, {str(ex)}")
            error = ex

        # At this point, we've caught an exception and stored it in 'error'

        # Display traceback in verbose mode
        if verbose:
            traceback.print_exc()

            # Raise a CLI application exception with the original error
            error_msg = (
                f"Failed to install CLI utility. name: {name}, ex: {error.__class__.__name__}, message: {str(error)}"
            )
            logger.critical(error_msg)
            raise CliApplicationException(error)
        else:
            # For non-verbose mode, provide a user-friendly error without traceback
            error_msg = f"name: {name}, exception: {error.__class__.__name__}, message: {str(error)}"
            error_msg += """\n\nPlease check the logs for more details, or run with --verbose (-v) flag.
For remote execution, please use flag --verbosity Verbose to see remote host logs."""
            raise click.ClickException(error_msg)


#     @staticmethod
#     def eval_installer_cli_entrypoint_pyfn_step(name: str, call: Callable, verbose: bool = False) -> None:
#         logger.debug(f"starting eval_installer_cli_entrypoint_pyfn_step: {name}")
#         is_failure = False
#         response = None
#         raised = None

#         try:
#             # Add additional validation
#             if call is None:
#                 logger.critical("Call function is None")
#                 raise ValueError("Call function cannot be None")

#             response = call()
#             logger.debug(f"call executed successfully, response: {response}")

#             # Verify the response
#             if response is None:
#                 logger.debug(f"Response from {name} is None, but no exception was raised")

#         except StepEvaluationFailure as sef:
#             is_failure = True
#             # logger.critical(f"StepEvaluationFailure: {str(sef)}")
#             print(str(sef))
#         except TypeError as te:
#             is_failure = True
#             logger.critical(f"TypeError: {str(te)}")
#             if "NoneType" in str(te):
#                 logger.critical("NoneType error detected, likely an unexpected None value was returned or accessed")
#             if verbose:
#                 traceback.print_exc()
#             raised = te
#         except Exception as ex:
#             is_failure = True
#             logger.critical(f"Exception occurred: {ex.__class__.__name__}, {str(ex)}")
#             if verbose:
#                 traceback.print_exc()
#             raised = ex

#         if verbose and is_failure:
#             error_msg = f"Failed to install CLI utility. name: {name}, ex: {raised.__class__.__name__}"
#             if raised is not None:
#                 error_msg += f", message: {str(raised)}"
#             else:
#                 error_msg += ", message: <No error message available>"

#             logger.critical(error_msg)

#             # If raised is None, create a descriptive exception
#             if raised is None:
#                 raised = Exception(f"Unknown error occurred during {name}. Check logs for details.")

#             raise CliApplicationException(raised)
#         elif is_failure:
#             # logger.error(f"name: {name}, exception: {raised.__class__.__name__}, message: {str(raised)}")
#             error_msg = f"name: {name}, exception: "
#             if raised is not None:
#                 error_msg += f"{raised.__class__.__name__}, message: {str(raised)}"
#             else:
#                 error_msg += "Unknown, message: <No error message available>"

#             error_msg += f"""\n\nPlease check the logs for more details, or run with --verbose (-v) flag.
# For remote execution, please use flag --verbosity Verbose to see remote host logs."""
#             raise click.ClickException(error_msg)

# if verbose and (is_failure or not response):
#     logger.critical(
#         f"Failed to install CLI utility. name: {name}, ex: {raised.__class__.__name__}, message: {str(raised)}"
#     )
#     if should_re_raise and verbose:
#         raise CliApplicationException(raised)
