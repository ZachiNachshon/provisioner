#!/usr/bin/env python3

from typing import Any, List, Set

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.prompter import Prompter, PromptLevel


class FakePrompter(Prompter):

    __registered_enter_prompt_counts: int = None
    __registered_yes_no_prompts: List[str] = None
    __registered_user_input_prompts: Set[str] = None
    __registered_user_single_selection_prompts: List[str] = None
    __registered_user_multi_selection_prompts: List[str] = None

    __mocked_yes_no_response: dict[str, bool] = None
    __mocked_user_input_response: dict[str, str] = None
    __mocked_user_single_selection_response: dict[str, Any] = None
    __mocked_user_multi_selection_response: dict[str, List[Any]] = None

    def __init__(self, auto_prompt: bool, dry_run: bool):
        super().__init__(auto_prompt=auto_prompt, dry_run=dry_run)
        self.__registered_enter_prompt_counts = 0
        self.__registered_yes_no_prompts = []
        self.__registered_user_input_prompts = []
        self.__registered_user_single_selection_prompts = []
        self.__registered_user_multi_selection_prompts = []
        self.__mocked_yes_no_response = {}
        self.__mocked_user_input_response = {}
        self.__mocked_user_single_selection_response = {}
        self.__mocked_user_multi_selection_response = {}

    @staticmethod
    def _create_fake(auto_prompt: bool, dry_run: bool) -> "FakePrompter":
        prompter = FakePrompter(auto_prompt, dry_run)
        prompter.prompt_user_multi_selection_fn = (
            lambda message, options: prompter._register_user_multi_selection_prompt(message)
        )
        prompter.prompt_user_single_selection_fn = (
            lambda message, options: prompter._register_user_single_selection_prompt(message, options)
        )
        prompter.prompt_user_input_fn = lambda message, default=None, redact_value=False, level=PromptLevel.HIGHLIGHT, post_user_input_message=None: prompter._register_user_input_prompt(
            message
        )
        prompter.prompt_yes_no_fn = lambda message, level=PromptLevel.INFO, post_yes_message=None, post_no_message=None: prompter._register_yes_no_prompt(
            message
        )
        prompter.prompt_for_enter_fn = lambda level=PromptLevel.INFO: prompter._register_enter_prompt()
        return prompter

    @staticmethod
    def create(ctx: Context) -> "FakePrompter":
        return FakePrompter._create_fake(auto_prompt=ctx.is_auto_prompt(), dry_run=ctx.is_dry_run())

    def _register_enter_prompt(self) -> bool:
        self.__registered_enter_prompt_counts += 1
        return True

    def assert_enter_prompt_count(self, count: int) -> None:
        if count != self.__registered_enter_prompt_counts:
            raise FakeEnvironmentAssertionError(
                f"Prompter expected a specific number of enter prompts which never fulfilled. count: {count}"
            )

    def mock_yes_no_response(self, prompt_str: str, response: bool):
        self.__mocked_yes_no_response[prompt_str] = response

    def _register_yes_no_prompt(self, prompt_str: str) -> bool:
        self.__registered_yes_no_prompts.append(prompt_str)
        for prompt in self.__mocked_yes_no_response:
            # prompt_str string might be longer than the mocked ones due to variables within the string
            if prompt in prompt_str:
                return prompt
        return None

    def assert_yes_no_prompt(self, message: str) -> None:
        found = False
        for prompt in self.__registered_yes_no_prompts:
            # prompt string might be longer that the asserted message due to variables within the string
            if message in prompt:
                found = True
                break
        if not found:
            raise FakeEnvironmentAssertionError(
                "Prompter expected a yes/no message but it never triggered. message: " + message
            )

    def mock_user_input_response(self, prompt_str: str, response: Any):
        self.__mocked_user_input_response[prompt_str] = response

    def _register_user_input_prompt(self, prompt_str: str) -> str:
        self.__registered_user_input_prompts.append(prompt_str)
        if prompt_str in self.__mocked_user_input_response:
            return self.__mocked_user_input_response[prompt_str]
        return None

    def assert_user_input_prompt(self, message: str) -> None:
        if message not in self.__registered_user_input_prompts:
            raise FakeEnvironmentAssertionError(
                "Prompter expected a user input message but it never triggered. message: " + message
            )

    def mock_user_single_selection_response(self, prompt_str: str, response: Any):
        self.__mocked_user_single_selection_response[prompt_str] = response

    def _register_user_single_selection_prompt(self, prompt_str: str, options: List[Any]) -> Any:
        self.__registered_user_single_selection_prompts.append(prompt_str)
        if prompt_str in self.__mocked_user_single_selection_response:
            return self.__mocked_user_single_selection_response[prompt_str]
        return options[0] if len(options) > 0 else None

    def assert_user_single_selection_prompt(self, message: str) -> None:
        if message not in self.__registered_user_single_selection_prompts:
            raise FakeEnvironmentAssertionError(
                "Prompter expected a user single selection message but it never triggered. message: " + message
            )

    def mock_user_multi_selection_response(self, prompt_str: str, responses: List[Any]):
        self.__mocked_user_multi_selection_response[prompt_str] = responses

    def _register_user_multi_selection_prompt(self, prompt_str: str) -> Any:
        self.__registered_user_multi_selection_prompts.append(prompt_str)
        if prompt_str in self.__mocked_user_multi_selection_response:
            return self.__mocked_user_multi_selection_response[prompt_str]
        return None

    def assert_user_multi_selection_prompt(self, message: str) -> None:
        if message not in self.__registered_user_multi_selection_prompts:
            raise FakeEnvironmentAssertionError(
                "Prompter expected a user multi selection message but it never triggered. message: " + message
            )
