#!/usr/bin/env python3

from abc import ABCMeta
from dataclasses import dataclass
from typing import Callable, Generic, NoReturn, TypeVar, Union

VAL = TypeVar("VAL")
ERR = TypeVar("ERR")

VAL1 = TypeVar("VAL1")
ERR1 = TypeVar("ERR1")

VAL2 = TypeVar("VAL2")
ERR2 = TypeVar("ERR2")

VAL3 = TypeVar("VAL3")
ERR3 = TypeVar("ERR3")

CALL_ERR = TypeVar("CALL_ERR")
CALL_VAL = TypeVar("CALL_VAL")


class Either(Generic[VAL, ERR], metaclass=ABCMeta):
    @staticmethod
    def left(error: ERR) -> "Either[ERR, NoReturn]":
        return Left(error)

    @staticmethod
    def right(value: VAL) -> "Either[NoReturn, VAL]":
        return Right(value)

    def require(
        self, predicate: Callable[[VAL1], bool], to_error: Callable[[VAL1], CALL_VAL]
    ) -> "Either[Union[VAL, CALL_VAL], VAL1]":
        def _case_right(right: Right[VAL1]) -> "Either[Union[VAL, CALL_VAL], VAL1]":
            if predicate(right.value):
                return right
            return Either.left(to_error(right.value))

        return self.match(lambda left: left, _case_right)

    def match(
        self, call_left: "Callable[[Left[ERR]], CALL_ERR]", call_right: "Callable[[Right[VAL]], CALL_VAL]"
    ) -> Union[CALL_ERR, CALL_VAL]:
        match self:
            case Left():
                return call_left(self)
            case Right():
                return call_right(self)
            case _:
                raise TypeError()

    def fold(
        self, call_left: "Callable[[ERR], CALL_ERR]", call_right: "Callable[[VAL], CALL_VAL]"
    ) -> Union[CALL_ERR, CALL_VAL]:
        return self.match(lambda error: call_left(error.value), lambda success: call_right(success.value))

    def map(self, func: Callable[[VAL], VAL1]) -> "Either[ERR, VAL1]":
        return self.match(lambda error: error, lambda success: Either.right(func(success.value)))

    def flat_map(self, func: "Callable[[VAL], Either[ERR1, VAL1]]") -> "Either[Union[ERR, ERR1], VAL1]":
        return self.match(lambda error: error, lambda success: func(success.value))

    def __lshift__(self, func: "Callable[[VAL], Either[ERR1, VAL1]]") -> "Either[Union[ERR, ERR1], VAL1]":
        return self.flat_map(func)


@dataclass(frozen=True)
class Left(Generic[ERR], Either[ERR, NoReturn]):
    value: ERR


@dataclass(frozen=True)
class Right(Generic[VAL1], Either[NoReturn, VAL1]):
    value: VAL1


def raise_exception(ex: BaseException) -> NoReturn:
    raise ex


class RaiseLeft(Generic[ERR], Exception):
    value: ERR


# class EitherMonad(Generic[VAL]):
#     def __lshift__(self, arg: Either[VAL, ERR]) -> VAL1:
#         return arg.fold(lambda error: raise_exception(RaiseLeft(error)), lambda success: success)
