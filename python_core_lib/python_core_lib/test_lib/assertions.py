#!/usr/bin/env python3

import json
import re
from typing import Any, Callable, List, Type
from unittest import mock

from click.testing import Result

from python_core_lib.test_lib.test_errors import CliRunnerTestError

REGEX_REMOTE_COLOR_CODES = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


class Assertion:
    @staticmethod
    def expect_call_argument(testObj, method_run_call: mock.MagicMock, arg_name: str, expected_value: Any) -> None:
        try:
            run_call_kwargs = method_run_call.call_args.kwargs
            call_arg = run_call_kwargs[arg_name]
            Assertion.expect_equal_objects(testObj, expected_value, call_arg)
        except Exception as ex:
            testObj.fail(f"Method call argument did not have the expected value. message: {str(ex)}")

    @staticmethod
    def expect_exists(testObj, method_run_call: mock.MagicMock, arg_name: str) -> None:
        try:
            run_call_kwargs = method_run_call.call_args.kwargs
            call_arg = run_call_kwargs[arg_name]
            testObj.assertIsNotNone(call_arg)
        except Exception as ex:
            testObj.fail(f"Method call was missing an argument. message: {str(ex)}")

    @staticmethod
    def expect_call_arguments(
        testObj, method_run_call: mock.MagicMock, arg_name: str, assertion_callable: Callable[..., Any]
    ) -> None:
        try:
            run_call_kwargs = method_run_call.call_args.kwargs
            call_arg = run_call_kwargs[arg_name]
            assertion_callable(call_arg)
        except Exception as ex:
            testObj.fail(f"Method call arguments did not have the expected values. message: {str(ex)}")

    @staticmethod
    def expect_raised_failure(testObj, ex_type: Type, method_to_run) -> None:
        failed = False
        try:
            output = method_to_run()
            if output and output.exit_code != 0:
                failed = True
                exception_class = output.exc_info[0]
                testObj.assertEqual(exception_class, ex_type)
        except Exception as ex:
            failed = True
            testObj.assertIsInstance(ex, ex_type)

        testObj.assertTrue(failed)

    @staticmethod
    def expect_output(testObj, expected: str, method_to_run) -> None:
        run_output = method_to_run()
        # Clear all ANSII color codes from output
        output_clear = REGEX_REMOTE_COLOR_CODES.sub("", run_output)
        # It won't get printed if the test pass
        print(output_clear)
        # Assert output
        testObj.assertIn(expected, output_clear)

    @staticmethod
    def expect_outputs(testObj, expected: List[str], method_to_run) -> None:
        run_output = method_to_run()
        if type(run_output) == Result:
            print(run_output)
            print(run_output.stdout)
            # print(run_output.stderr)
            raise CliRunnerTestError(run_output.stderr)
        else:
            # Clear all ANSII color codes from output
            output_clear = REGEX_REMOTE_COLOR_CODES.sub("", run_output)
            # It won't get printed if test passes
            print(output_clear)
            for item in expected:
                # Assert single output
                testObj.assertIn(item, output_clear)

    @staticmethod
    def expect_success(testObj, method_to_run) -> Any:
        output = None
        success = False
        try:
            output = method_to_run()
            success = True
        except Exception as ex:
            testObj.fail(f"Test was expected to pass. message: {str(ex)}")

        testObj.assertTrue(success)
        return output

    @staticmethod
    def expect_equal_objects(testObj, obj1, obj2):
        try:
            testObj.maxDiff = None
            obj1_json = to_json(obj1)
            obj2_json = to_json(obj2)
            testObj.assertEqual(obj1_json, obj2_json)
        except Exception as ex:
            testObj.fail(f"Objects are not equal or encountered a JSON serialization failure. message: {str(ex)}")
        return


def to_json(obj: Any) -> str:
    if hasattr(obj, "__dict__"):
        return json.dumps(obj.__dict__, default=vars, indent=2)
    else:
        return json.dumps(obj, default=vars, indent=2)
