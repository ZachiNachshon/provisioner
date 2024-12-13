#!/usr/bin/env python3

import typing
from typing import Any, Callable, List
from unittest.mock import MagicMock

from loguru import logger


class Anything:
    pass


class RegisteredMock:
    func_name: str
    args_hash: str
    mock: MagicMock

    def __init__(self, func_name: str, args_hash: str, mock: MagicMock):
        self.func_name = func_name
        self.args_hash = args_hash
        self.mock = mock


class TestFakes:

    __registered_mocks = List[RegisteredMock]

    def __init__(self):
        self.__registered_mocks: List[RegisteredMock] = []

    def try_extract_magic_mock_value(self, magic_mock: MagicMock):
        if magic_mock.side_effect is not None:
            print("trigerring side effect")
            return magic_mock.side_effect()
        elif magic_mock.return_value is not None:
            print("trigerring return value")
            return magic_mock.return_value
        else:
            print("The MagicMock does not have a mocked value")
            exit(1)

    # args are the actual values passed by the calling function
    def trigger_side_effect(self, func_name: str, *args) -> Any:
        fn_register_log_msg = f"Called: {self.__class__.__name__}.{func_name}("
        args_as_str = ""
        ordered_args = []
        for arg in args:
            if isinstance(arg, MagicMock):
                # Mocked object (potentialy from mock.patch)
                ordered_args.append(Anything())
                args_as_str += Anything.__name__
                fn_register_log_msg += f"{Anything.__name__}, "
            elif callable(arg) or hasattr(arg, "__call__"):
                # callable or function
                ordered_args.append(arg)
                args_as_str += Callable.__name__
                fn_register_log_msg += f"{Callable.__name__}, "
            else:
                if arg is None:
                    ordered_args.append(arg)
                    args_as_str += Anything.__name__
                    fn_register_log_msg += "Anything, "
                else:
                    ordered_args.append(arg)
                    args_as_str += type(arg).__name__
                    fn_register_log_msg += f"{type(arg).__name__}, "

        # Create a hash of the string
        args_hash = hash(args_as_str)

        # print("==========================")
        # print(f"hash: {args_hash}, args_str: {args_as_str}")
        # print("==========================")

        fn_register_log_msg = fn_register_log_msg.removesuffix(", ")
        logger.debug(fn_register_log_msg + ")")

        result = None
        idx = 0
        for registered_mock in self.__registered_mocks:
            if registered_mock.func_name == func_name and registered_mock.args_hash == args_hash:
                result = registered_mock.mock
                break
            idx += 1

        if not result:
            print(f"Definition is not mocked or mock was empty, cannot proceed. name: {func_name}")
            exit(1)
        else:
            # Remove the mock call from the list, do not do that from the loop
            self.__registered_mocks.pop(idx)
            # Trigger the mock call
            return result(*ordered_args)

    def on(self, func_name: str, *args) -> MagicMock:
        if not self.__is_dict_initialized_and_nonempty(self.__registered_mocks):
            print(
                "TestFakes.__registered_mocks is None, forgot to call TestFakes.__init__(self) from the fake test class? Exiting..."
            )
            exit(1)

        fn_register_log_msg = f"Registered: {self.__class__.__name__}.{func_name}("
        args_as_str = ""
        # Loop through the types passed in *args
        for arg in args:
            #  TODO: Check if callable and allow it !!
            if isinstance(arg, type):
                if arg is Anything:
                    args_as_str += Anything.__name__
                    fn_register_log_msg += "Anything, "
                else:
                    # Check if the argument is a type
                    args_as_str += arg.__name__
                    fn_register_log_msg += f"{arg.__name__}, "
            # Check if the argument is a List, Dict, Tuple etc..
            elif arg is typing.List:
                args_as_str += list.__name__
                fn_register_log_msg += f"{list.__name__}, "
            elif arg is typing.Dict:
                args_as_str += dict.__name__
                fn_register_log_msg += f"{dict.__name__}, "
            elif arg is typing.Tuple:
                args_as_str += tuple.__name__
                fn_register_log_msg += f"{tuple.__name__}, "
            elif arg is Callable or callable(arg):
                print(type(arg).__name__)
                print(arg.__name__)
                args_as_str += Callable.__name__
                fn_register_log_msg += "Callable, "
            else:
                print(f"Invalid mocked argument, should be typed. name: {func_name}, mocked args: {args}")
                exit(1)

        mock_obj = MagicMock()
        reg_mock = RegisteredMock(func_name, hash(args_as_str), mock_obj)
        self.__registered_mocks.append(reg_mock)

        fn_register_log_msg = fn_register_log_msg.removesuffix(", ")
        logger.debug(fn_register_log_msg + ")")

        # print("==========================")
        # print(f"hash: {hash(args_as_str)}, args_str: {args_as_str}")
        # print("==========================")
        return mock_obj

    def __is_dict_initialized_and_nonempty(self, d) -> bool:
        return d is not None and isinstance(d, List)
