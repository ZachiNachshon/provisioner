#!/usr/bin/env python3

from typing import Any, List, Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.prompter import Prompter, PromptLevel


class FakePrompter(TestFakes, Prompter):
    def __init__(self, auto_prompt: bool, dry_run: bool):
        TestFakes.__init__(self)
        Prompter.__init__(self, auto_prompt=auto_prompt, dry_run=dry_run)

    @staticmethod
    def create(ctx: Context) -> "FakePrompter":
        fake = FakePrompter(auto_prompt=ctx.is_auto_prompt(), dry_run=ctx.is_dry_run())
        fake.prompt_user_multi_selection_fn = MagicMock(side_effect=fake.prompt_user_multi_selection_fn)
        fake.prompt_user_single_selection_fn = MagicMock(side_effect=fake.prompt_user_single_selection_fn)
        fake.prompt_user_input_fn = MagicMock(side_effect=fake.prompt_user_input_fn)
        fake.prompt_yes_no_fn = MagicMock(side_effect=fake.prompt_yes_no_fn)
        fake.prompt_for_enter_fn = MagicMock(side_effect=fake.prompt_for_enter_fn)
        return fake

    def prompt_user_multi_selection_fn(self, message: str, options: List[Any]) -> Any:
        return self.trigger_side_effect("prompt_user_multi_selection_fn", message, options)

    def prompt_user_single_selection_fn(self, message: str, options: List[Any]) -> Any:
        return self.trigger_side_effect("prompt_user_single_selection_fn", message, options)

    def prompt_user_input_fn(
        self,
        message: str,
        default: Optional[str] = None,
        redact_value: Optional[bool] = False,
        level: Optional[PromptLevel] = PromptLevel.HIGHLIGHT,
        post_user_input_message: Optional[str] = None,
    ) -> str:
        return self.trigger_side_effect(
            "prompt_user_input_fn", message, default, redact_value, level, post_user_input_message
        )

    def prompt_yes_no_fn(
        self,
        message: str,
        level: Optional[PromptLevel] = PromptLevel.HIGHLIGHT,
        post_yes_message: Optional[str] = None,
        post_no_message: Optional[str] = None,
    ) -> bool:
        return self.trigger_side_effect("prompt_yes_no_fn", message, level, post_yes_message, post_no_message)

    def prompt_for_enter_fn(self, level: Optional[PromptLevel] = PromptLevel.INFO) -> bool:
        return self.trigger_side_effect("prompt_for_enter_fn", level)
