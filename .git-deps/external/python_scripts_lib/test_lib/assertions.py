#!/usr/bin/env python3

from typing import Any, Type


class Assertion:
    @staticmethod
    def expect_failure(testObj, ex_type: Type, methodToRun) -> None:
        failed = False
        try:
            methodToRun()
        except Exception as ex:
            failed = True
            testObj.assertIsInstance(ex, ex_type)

        testObj.assertTrue(failed)

    @staticmethod
    def expect_success(testObj, methodToRun) -> Any:
        output = None
        success = False
        try:
            output = methodToRun()
            success = True
        except Exception as ex:
            testObj.fail(f"Test was expected to pass. message: {str(ex)}")

        testObj.assertTrue(success)
        return output
