#!/usr/bin/env python3


class FakeEnvironmentAssertionError(Exception):
    pass


class CliRunnerTestError(Exception):
    pass


class DefinitionIsNotMockedError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
