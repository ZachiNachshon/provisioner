#!/usr/bin/env python3

import unittest

from python_core_lib.func.either import ERR, VAL
from python_core_lib.func.environment import PyFnEnvBase
from python_core_lib.func.pyfn import PyFn, PyFnEvaluator
from python_core_lib.infra.context import Context
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.shared.collaborators_fakes import FakeCoreCollaborators
from python_core_lib.utils.os import MAC_OS, OsArch


# To run as a single test target:
#  poetry run coverage run -m pytest python_core_lib/func/pyfn_test.py
#
class PyFnTestShould(unittest.TestCase):
    class TestArgs:
        name: str
        value: int

        def __init__(self, name: str, value: int = 0) -> None:
            self.name = name
            self.value = value

    class TestEnv(PyFnEnvBase):

        args: "PyFnTestShould.TestArgs"

        def __init__(self, ctx: Context, collaborators: CoreCollaborators, args: "PyFnTestShould.TestArgs") -> None:
            super().__init__(ctx=ctx)
            self.collaborators = collaborators
            self.args = args

    def create_call_chain(self, count: int) -> "PyFn[object, ERR, VAL]":
        chain = PyFn.success(1)
        for i in range(count - 1):
            chain = (
                chain.map(lambda n: n + 1)
                .flat_map(lambda n: PyFn.success(n - 1))
                .map(lambda n: n + 1)
                .map(lambda n: n - 1)
                .flat_map(lambda n: PyFn.success(n + 1))
                .flat_map(lambda n: PyFn.success(n - 1))
                .map(lambda n: n + 1)
            )
        return chain

    def create_fake_env(self, verbose: bool = False) -> PyFnEnvBase:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS), verbose=verbose)
        return PyFnTestShould.TestEnv(
            ctx=ctx, collaborators=FakeCoreCollaborators(ctx), args=PyFnTestShould.TestArgs("test-name")
        )

    def test_pyfn_with_shift(self):
        pyfn = PyFnEvaluator.new(env=self.create_fake_env())
        var = pyfn << self.create_call_chain(10)
        self.assertEqual(var, 10)

    def test_pyfn_with_compose(self):
        pyfn = PyFnEvaluator.new(env=self.create_fake_env())
        var = pyfn.eval(self.create_call_chain(10))
        self.assertEqual(var, 10)

    def test_pyfn_without_invocation(self):
        chain = self.create_call_chain(10)
        self.assertIsNotNone(chain)
        self.assertIsInstance(chain, PyFn)

    def test_pyfn_for_each(self):
        items = [1, 2, 3, 4, 5]
        result = [2, 4, 6, 8, 10]
        chain = PyFn.of(items).for_each(lambda item: PyFn.of(item * 2))
        pyfn = PyFnEvaluator.new(env=self.create_fake_env(verbose=True))
        var = pyfn << chain
        self.assertIsInstance(chain, PyFn)
        self.assertEqual(var, result)
        # self.assertTrue(False)

    def test_pyfn_filter(self):
        items = [1, 2, 3, 4, 5, 6]
        result = [2, 4, 6]
        chain = PyFn.of(items).filter(lambda item: item % 2 == 0)
        pyfn = PyFnEvaluator.new(env=self.create_fake_env())
        var = pyfn << chain
        self.assertIsInstance(chain, PyFn)
        self.assertEqual(var, result)

    def test_pyfn_if_then_else(self):
        chain = PyFn.success(2).if_then_else(
            predicate=lambda num: num % 2 == 0, if_true=lambda _: PyFn.of("even"), if_false=lambda _: PyFn.of("odd")
        )
        pyfn = PyFnEvaluator.new(env=self.create_fake_env())
        var = pyfn << chain
        self.assertIsNotNone(var)
        self.assertIsInstance(chain, PyFn)
        self.assertEqual(var, "even")

    def test_pyfn_debug(self):
        chain = PyFn.success(1)
        chain = chain.map(lambda n: n + 1).debug("test {value}").map(lambda n: n + 1).debug("{value} test {value}")
        pyfn = PyFnEvaluator.new(env=self.create_fake_env(verbose=True))
        var = pyfn << chain
        self.assertIsNotNone(var)
        self.assertIsInstance(chain, PyFn)
        self.assertEqual(var, 3)
        # self.assertTrue(False)

    # def test_pyfn_if_then_else_with_for_each(self):
    #     items = [1, 2, 3, 4, 5]
    #     result = []
    #     chain = PyFn.of(items).for_each(lambda item: )
    #     chain = PyFn.success(2).if_then_else(
    #             predicate=lambda num: num % 2 == 0,
    #             if_true=PyFn.of("even"),
    #             if_false=PyFn.of("odd")
    #     )
    #     pyfn = PyFnEvaluator.new(env=self.create_fake_env())
    #     var = pyfn << chain
    #     # print("chain: " + str(type(chain)))
    #     # print("chain_cont (type): " + str(type(chain_cont)))
    #     # print("chain_cont (value): " + str(chain_cont))
    #     self.assertIsNotNone(var)
    #     self.assertIsInstance(chain, PyFn)
    #     self.assertEqual(var, "even")

    # def test_pyfn_if_then_else(self):
    #     chain = PyFn.success(0)
    #     items = [1, 2, 3, 4, 5]
    #     result = []

    #     def predicate(item: int) -> bool:
    #         print("pred: " + str(item))
    #         print("pred v: " + str(item % 2 == 0))
    #         return item % 2 == 0

    #     def print_and_return(item: int) -> int:
    #         print("effect: " + str(item))
    #         return item

    #     for item in items:
    #         temp = PyFn.empty().map(lambda _: predicate(item)).if_then_else(
    #             # if_call=PyFn.effect(lambda: item),
    #             if_true=PyFn.effect(lambda: print_and_return(item)),
    #             if_false=PyFn.effect(lambda: print_and_return(item))
    #             # else_call=PyFn.effect(lambda: item)
    #             # else_call=PyFn.empty()
    #         )
    #         chain = chain.flat_map(lambda _: temp)

    #     pyfn = PyFnEvaluator.new(env=self.create_fake_env())
    #     var = pyfn << chain
    #     print(var)
    #     print(result)
    #     self.assertIsNotNone(var)
    #     self.assertIsInstance(chain, PyFn)
    #     self.assertTrue(False)
