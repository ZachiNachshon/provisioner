#!/usr/bin/env python3

from enum import Enum
from typing import Optional
from loguru import logger

from ..colors import color
from ..infra.context import Context


class PromptLevel(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3


class Prompter:

    _auto_prompt: bool = None

    def __init__(self, auto_prompt: bool) -> None:
        self._auto_prompt = auto_prompt

    @staticmethod
    def create(ctx: Context) -> "Prompter":
        auto_prompt = ctx.is_auto_prompt()
        logger.debug(f"Creating an input prompter (auto_prompt: {auto_prompt})...")
        return Prompter(auto_prompt)

    def _prompt_user_input(self, message: str, default: Optional[str] = None) -> str:
        if self._auto_prompt:
            logger.debug("Auto-prompt mode.")
            return "AUTO_PROMPT_RESPONSE"

        enriched_msg = "{} (enter to abort): ".format(message)
        if default is not None:
            enriched_msg = "{} (default: {}): ".format(message, default)

        output = input(enriched_msg)
        if output:
            return output
        elif default is not None:
            return default

        return ""

    def _prompt_yes_no(self, message: str, level: Optional[PromptLevel] = PromptLevel.INFO) -> bool:
        if self._auto_prompt:
            logger.debug("Auto-prompt mode.")
            return True

        msg_fmt = "{}" + message + " ? (y/n): {}"
        color_in_use = color.NONE

        if level == PromptLevel.CRITICAL:
            color_in_use = color.RED
        elif level == PromptLevel.WARNING:
            color_in_use = color.YELLOW

        prompt = msg_fmt.format(color_in_use, color.NONE)
        output = input(prompt)
        return output and output == "y"

    prompt_user_input_fn = _prompt_user_input
    prompt_yes_no_fn = _prompt_yes_no
