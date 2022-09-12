#!/usr/bin/env python3

from ..infra.context import Context
from .prompter import Prompter, PromptLevel


class FakePrompter(Prompter):

    yes_no_response: bool = None

    def __init__(self, auto_prompt: bool):
        super().__init__(auto_prompt=auto_prompt)
        self.yes_no_response = True

    @staticmethod
    def _create_fake(auto_prompt: bool) -> "FakePrompter":
        prompter = FakePrompter(auto_prompt)
        prompter.prompt_user_input_fn = lambda message, default=None: default if default else ""
        prompter.prompt_yes_no_fn = lambda message, level=PromptLevel.INFO: prompter.yes_no_response
        return prompter

    @staticmethod
    def create(ctx: Context) -> "FakePrompter":
        return FakePrompter._create_fake(auto_prompt=ctx.is_auto_prompt())

    def set_yes_no_response(self, response: bool) -> None:
        self.yes_no_response = response
