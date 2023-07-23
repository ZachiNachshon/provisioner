#!/usr/bin/env python3

from functools import reduce
from typing import Callable, Generic, List, NoReturn, Type, TypeVar, Union

from loguru import logger

from python_core_lib.func.either import Either, Left, Right, raise_exception
from python_core_lib.func.environment import PyFnEnvBase

# PyFn Types
ENV = TypeVar("ENV", bound=PyFnEnvBase)  # Environment
ERR = TypeVar("ERR", bound=Exception)  # Error
VAL = TypeVar("VAL")  # Value

ENV1 = TypeVar("ENV1", bound=PyFnEnvBase)  # Environment
ERR1 = TypeVar("ERR1", bound=Exception)  # Error
ERR2 = TypeVar("ERR2", bound=Exception)  # Error
ERR3 = TypeVar("ERR3", bound=Exception)  # Error
VAL1 = TypeVar("VAL1")  # Value
VAL2 = TypeVar("VAL2")  # Value
VAL3 = TypeVar("VAL3")  # Value

EX = TypeVar("EX", bound=BaseException)


class PyFnEvaluator(Generic[ENV, ERR1]):

    _environment: ENV

    def __init__(self, environment: ENV) -> None:
        self._environment = environment

    def __lshift__(self, arg: "PyFn[ENV, ERR1, VAL1]") -> VAL1:
        return self.eval(arg)

    def eval(self, arg: "PyFn[ENV, ERR1, VAL1]") -> VAL1:
        # This is the actual evaluation of the PyFn call chain
        return arg._run(self._environment).fold(
            # lambda error: raise_exception(RaiseLeft(error)), lambda success: success
            lambda error: raise_exception(error),
            lambda success: success,
        )

    def new(env: ENV) -> "PyFnEvaluator[ENV, ERR1]":
        return PyFnEvaluator(environment=env)


class PyFn(Generic[ENV, ERR, VAL]):

    _run: Callable[[ENV], Either[ERR, VAL]]

    """
    ENV, ERR, VAL - those are the types that the current PyFn object was created with.
    It is an immutable object.
    When generating new objects using the statis functions, we need to address those
    types as new ones, hence the XXX1 suffix.
    """

    def __init__(self, run: Callable[[ENV], Either[ERR, VAL]]):
        """
        Every PyFn object must have the following callback structure:
          environment --> Either(error, success)
        To chain PyFn objects, each of them must be able to have that function signature
        in their constructor.
        """
        self._run = run

    @staticmethod
    def empty() -> "PyFn[object, NoReturn, VAL1]":
        return PyFn.success(None)

    @staticmethod
    def of(value: VAL1) -> "PyFn[object, NoReturn, VAL1]":
        return PyFn.success(value)

    @staticmethod
    def success(value: VAL1) -> "PyFn[object, NoReturn, VAL1]":
        return PyFn(lambda _: Right(value))

    @staticmethod
    def fail(error: ERR1) -> "PyFn[object, ERR1, NoReturn]":
        return PyFn(lambda _: Left(error))

    @staticmethod
    def effect(side_effect: Callable[[], VAL1]) -> "PyFn[object, Exception, VAL1]":
        return PyFn[object, NoReturn, VAL1](lambda _: Either.right(side_effect())).catch(Exception)

    def map(self, func: Callable[[VAL], VAL1]) -> "PyFn[ENV, ERR, VAL1]":
        """
        Function from a value to an Either object
        """
        return PyFn(lambda env: self._run(env).map(func))

    def flat_map(self, func: Callable[[VAL], "PyFn[ENV1, ERR1, VAL1]"]) -> "PyFn[ENV1, Union[ERR, ERR1], VAL1]":
        """
        Function from a value to a PyFn object
        The flatmap in this case recieves an environment and returns an Either object
        """
        return PyFn(lambda env: self._run(env).flat_map(lambda value: func(value)._run(env)))

    def __lshift__(self: "PyFn[ENV1, ERR, VAL1]", other: "PyFn[ENV1, ERR, VAL1]") -> "PyFn[ENV1, ERR, VAL1]":
        return self.flat_map(lambda _: other)

    def _filter(self, iterator, predicate: Callable[[VAL1], bool]) -> "PyFn[ENV1, ERR1, List[VAL1]]":
        result = []
        for item in iterator:
            if predicate(item):
                result.append(item)
        return PyFn.success(result)

    def filter(self, func: Callable[[VAL1], bool]) -> "PyFn[ENV1, ERR1, List[VAL1]]":
        return PyFn(lambda env: self._run(env).flat_map(lambda iterable: self._filter(iter(iterable), func)._run(env)))

    def _for_each(
        self, env: ENV, iterable, func: Callable[[VAL1], "PyFn[ENV1, ERR2, VAL2]"]
    ) -> "PyFn[ENV1, ERR1, List[VAL1]]":
        result: List[VAL2] = []

        def collect_and_return_value(value):
            if env.ctx.is_verbose():
                logger.debug(f"PyFn for_each iteration: {value}")
            result.append(value)
            return value

        chain_list = map(lambda item: func(item), iterable)
        call_chain = reduce(
            lambda call_1, call_2: call_1.flat_map(lambda value: PyFn.of(collect_and_return_value(value))).flat_map(
                lambda _: call_2
            ),
            chain_list,
        )
        return call_chain.flat_map(lambda value: PyFn.of(collect_and_return_value(value))).map(lambda _: result)

    def for_each(self, func: Callable[[VAL1], "PyFn[ENV1, ERR1, VAL2]"]) -> "PyFn[ENV1, ERR1, List[VAL1]]":
        return PyFn(
            lambda env: self._run(env).flat_map(lambda iterable: self._for_each(env, iter(iterable), func)._run(env))
        )

    def _log_and_return_value(self, message: str, value: VAL1) -> "PyFn[ENV1, ERR1, VAL1]":
        return PyFn.effect(lambda: logger.debug(message.format(value=value))).map(lambda _: value)

    def _chain_debug_if_verbose(self, env: ENV, message: str) -> Either[ERR, VAL]:
        if env.ctx and env.ctx.is_verbose():
            return self._run(env).flat_map(lambda value: self._log_and_return_value(message, value)._run(env))
        else:
            return self._run(env)

    def debug(self, message: str) -> "PyFn[ENV1, ERR, VAL]":
        return PyFn(lambda env: self._chain_debug_if_verbose(env, message))

    def _if_then_else(
        self,
        value: VAL,
        predicate: Callable[[VAL], bool],
        if_true: Callable[[VAL], "PyFn[ENV1, ERR1, VAL1]"],
        if_false: Callable[[VAL], "PyFn[ENV1, ERR2, VAL2]"],
    ) -> "PyFn[ENV1, Union[ERR1, ERR2], Union[VAL1, VAL2]]":
        return (
            PyFn.of(value)
            .map(predicate)
            .flat_map(lambda pred_val: self._match_bool(value, pred_val, if_true, if_false))
        )

    def if_then_else(
        self,
        predicate: Callable[[VAL], bool],
        if_true: Callable[[VAL], "PyFn[ENV1, ERR1, VAL1]"],
        if_false: Callable[[VAL], "PyFn[ENV1, ERR2, VAL2]"],
    ) -> "PyFn[ENV1, Union[ERR1, ERR2], Union[VAL1, VAL2]]":
        return PyFn(
            lambda env: self._run(env).flat_map(
                lambda value: self._if_then_else(value, predicate, if_true, if_false)._run(env)
            )
        )

    def _match_bool(
        self,
        value: VAL,
        pred_val: bool,
        if_true: Callable[[VAL], "PyFn[ENV1, ERR1, VAL1]"],
        if_false: Callable[[VAL], "PyFn[ENV1, ERR2, VAL2]"],
    ) -> "PyFn[ENV1, Union[ERR1, ERR2], Union[VAL1, VAL2]]":
        match pred_val:
            case True:
                return if_true(value)
            case False:
                return if_false(value)
            case _:
                raise TypeError(f"Type matching expected bool but recieved {type(value)}")

    def catch(self: "PyFn[ENV, ERR, VAL1]", exception: Type[EX]) -> "PyFn[ENV, Union[ERR, EX], VAL1]":
        def _maybe_fail_fn(env: ENV) -> Either[Union[ERR, EX], VAL1]:
            try:
                return self._run(env)
            except exception as ex:
                return Either.left(error=ex)

        return PyFn(_maybe_fail_fn)


class Environment(Generic[ENV], PyFn[ENV, NoReturn, ENV]):
    _run: Callable[[ENV], Right[ENV]]

    def __init__(self) -> None:
        self._run = lambda env: Right(env)
