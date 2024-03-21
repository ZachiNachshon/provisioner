#!/usr/bin/env python3

from typing import Any
from unittest.mock import MagicMock

class Anything():
    pass

class TestFakes:

    __funcs_dict = dict[str, dict[str, MagicMock]]

    def __init__(self):
        self.__funcs_dict = {}


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
    def trigger_side_effect(self, func_name: str, *args)-> None:
        args_as_str = ""
        ordered_args = []
        for arg in args:
            if isinstance(arg, MagicMock):
                # ret_val = self.try_extract_magic_mock_value(arg)
                # print(f"arg ret val: {ret_val}")
                print("Appending faker.Anything()")
                # ordered_args.append(ret_val)
                ordered_args.append(Anything())
            else:
                print("arg is not a MagicMock")
                print(type(arg).__name__)
                ordered_args.append(arg)
                args_as_str += type(arg).__name__

        # Create a hash of the string
        args_hash = hash(args_as_str)

        # print("==========================")
        # print(args_hash)
        # print(self.__funcs_dict)
        # print("==========================")

        result = None
        # Get the function input dictionary
        if self.__funcs_dict.get(func_name):
            func_hash_dict = self.__funcs_dict[func_name]
            if func_hash_dict.get(args_hash):
                result = func_hash_dict.pop(args_hash, None)
                if result:
                    print("FINAL ARGS:")
                    print(*ordered_args)
                    result(*ordered_args)
                    # result("asdf", "asdfsdf")
                else:
                    print(f"Definition was defined but mock is empty, cannot proceed. name: {func_name}")
                    exit(1)
            else:
                print(f"Definition was defined but mock is empty, check that mocked method types is correct, cannot proceed. name: {func_name}")
                exit(1)
        else:
            print(f"Definition is not mocked, cannot proceed. name: {func_name}")
            exit(1)

    def on(self, func_name: str, *args) -> MagicMock:
        if not self.__is_dict_initialized_and_nonempty(self.__funcs_dict):
            print("TestFakes.__funcs_dict is None, forgot to call TestFakes.__init__(self) from the fake test class? Exiting...")
            exit(1)

        args_as_str = ""
        # Loop through the types passed in *args
        for arg in args:
            if isinstance(arg, type):
                if arg is not Anything:
                    print(arg.__name__)
                    # Check if the argument is a type
                    if isinstance(arg, type):
                        args_as_str += arg.__name__
                else:
                    print("Skipping Anything type...")
            
            
            #  TODO: Check if callable and allow it !!
                    
                    
            else:
                print(f"Invalid mocked argument, should be typed. name: {func_name}, mocked args: {args}")
                exit(1)
            

        # Create a hash of the string
        args_hash = hash(args_as_str)

        # Create a mock mapping for the input
        args_mock = MagicMock()    
        args_hash_to_mock_dict_new = {args_hash: args_mock}

        maybe_func: dict[Any, MagicMock] = self.__funcs_dict.get(func_name)
        if maybe_func:
            args_hash_to_mock_dict = maybe_func.get(args_hash)
            if args_hash_to_mock_dict:
                # If the input is already registered, we append to the list of side effects
                args_hash_to_mock_dict[args_hash] = args_mock
            else:
                # For cases of functions without an input
                # If the input is not registered, we create a new input dict
                maybe_func[func_name] = args_hash_to_mock_dict_new
        else:
            # If the function is not registered, we create a new function dict
            self.__funcs_dict[func_name] = args_hash_to_mock_dict_new


        # print("==========================")
        # print(args_hash)
        # print(self.__funcs_dict)
        # print("==========================")
        return args_mock

    def __is_dict_initialized_and_nonempty(self, d) -> bool:
        return d is not None and isinstance(d, dict)
    