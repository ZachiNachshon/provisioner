#!/usr/bin/env python3

from typing import Any, List

from ..infra.context import Context
from .prompter import Prompter, PromptLevel


class FakePrompter(Prompter):

    press_enter_response: bool = None
    registered_yes_no_prompts: dict[str, bool] = None
    registered_user_input_prompts: dict[str, str] = None
    registered_user_selection_prompts: dict[str, Any] = None

    def __init__(self, auto_prompt: bool, dry_run: bool):
        super().__init__(auto_prompt=auto_prompt, dry_run=dry_run)
        self.press_enter_response = True
        self.registered_yes_no_prompts = {}
        self.registered_user_input_prompts = {}
        self.registered_user_selection_prompts = {}

    @staticmethod
    def _create_fake(auto_prompt: bool, dry_run: bool) -> "FakePrompter":
        prompter = FakePrompter(auto_prompt, dry_run)
        prompter.prompt_user_selection_fn = lambda message, options, multi_select=False: prompter._user_selection_prompt_selector(message)
        prompter.prompt_user_input_fn = lambda message, default=None, redact_default=False, level=PromptLevel.HIGHLIGHT, post_user_input_message=None: prompter._user_input_prompt_selector(
            message
        )
        prompter.prompt_yes_no_fn = lambda message, level=PromptLevel.INFO, post_yes_message=None, post_no_message=None: prompter._yes_no_prompt_selector(
            message
        )
        prompter.prompt_for_enter_fn = lambda level=PromptLevel.INFO: prompter.press_enter_response
        return prompter

    @staticmethod
    def create(ctx: Context) -> "FakePrompter":
        return FakePrompter._create_fake(
            auto_prompt=ctx.is_auto_prompt(),
            dry_run=ctx.is_dry_run())

    def register_yes_no_prompt(self, prompt_str: str, expected_output: bool):
        self.registered_yes_no_prompts[prompt_str] = expected_output

    def _yes_no_prompt_selector(self, message: str) -> str:
        for key, value in self.registered_yes_no_prompts.items():
            if message.__contains__(key):
                return value
        raise LookupError("Fake prompter yes/no message is not defined. prompt: " + message)

    def register_user_input_prompt(self, prompt_str: str, expected_output: str):
        self.registered_user_input_prompts[prompt_str] = expected_output

    def _user_input_prompt_selector(self, message: str) -> str:
        for key, value in self.registered_user_input_prompts.items():
            if message.__contains__(key):
                return value
        raise LookupError("Fake prompter user input message is not defined. prompt: " + message)

    def register_user_selection_prompt(self, prompt_str: str, expected_output: Any):
        self.registered_user_selection_prompts[prompt_str] = expected_output

    def _user_selection_prompt_selector(self, message: str) -> Any:
        for key, value in self.registered_user_selection_prompts.items():
            if message.__contains__(key):
                return value
        raise LookupError("Fake prompter user selection message is not defined. prompt: " + message)
