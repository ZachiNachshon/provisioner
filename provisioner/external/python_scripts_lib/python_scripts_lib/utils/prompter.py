#!/usr/bin/env python3

from enum import Enum
from typing import Any, List, Optional

import inquirer
from inquirer.themes import GreenPassion
from loguru import logger

from ..colors import color
from ..infra.context import Context

GO_UP_ONE_LINE = "\033[1A"
DELETE_LINE_TO_BEGINNING = "\033[K"
CHECKMARK_ICON = "✔"
CROSSMARK_ICON = "✘"


class PromptLevel(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    HIGHLIGHT = 4


class Prompter:

    _auto_prompt: bool = None
    _dry_run: bool = None

    def __init__(self, auto_prompt: bool, dry_run: bool) -> None:
        self._auto_prompt = auto_prompt
        self._dry_run = dry_run

    @staticmethod
    def create(ctx: Context) -> "Prompter":
        auto_prompt = ctx.is_auto_prompt()
        dry_run = ctx.is_dry_run()
        logger.debug(f"Creating an input prompter (auto_prompt: {auto_prompt}, dry_run: {dry_run})...")
        return Prompter(auto_prompt, dry_run)

    def _clear_previous_line(self, count: Optional[int] = 1):
        clear_format = ""
        for line in range(count):
            clear_format += f"{GO_UP_ONE_LINE}{DELETE_LINE_TO_BEGINNING}"
        print(clear_format)

    def _overwrite_previous_line(self, message: str, color_in_use: str, icon: Optional[str] = None):
        msg_format = ""
        if icon:
            msg_format += f"{GO_UP_ONE_LINE}{color_in_use}{icon} {message}{color.NONE}{DELETE_LINE_TO_BEGINNING}"
        else:
            msg_format += f"{GO_UP_ONE_LINE}{color_in_use}{message}{color.NONE}{DELETE_LINE_TO_BEGINNING}"
        print(msg_format)

    def _get_color_from_prompt_level(self, level: PromptLevel) -> str:
        color_in_use = color.NONE
        if level == PromptLevel.HIGHLIGHT:
            color_in_use = color.LIGHT_CYAN
        elif level == PromptLevel.CRITICAL:
            color_in_use = color.RED
        elif level == PromptLevel.WARNING:
            color_in_use = color.YELLOW
        return color_in_use

    def _prompt_user_input(
        self,
        message: str,
        default: Optional[str] = None,
        redact_default: Optional[bool] = False,
        level: Optional[PromptLevel] = PromptLevel.HIGHLIGHT,
        post_user_input_message: Optional[str] = None,
    ) -> str:

        if self._dry_run:
            logger.debug(f"{message}: Dry-run mode.")
            return "DRY_RUN_RESPONSE"

        if self._auto_prompt:
            logger.debug(f"{message}: Auto-prompt mode.")
            return default

        enriched_msg = "{} (enter to abort): ".format(message)
        if default is not None:
            enriched_msg = "{} (default: {}): ".format(message, "REDACTED" if redact_default else default)

        color_in_use = self._get_color_from_prompt_level(level)
        prompt = f"{color_in_use}{enriched_msg}{color.NONE}"
        user_input = input(prompt)

        if user_input:
            if post_user_input_message:
                self._overwrite_previous_line(
                    message=f"{post_user_input_message}{user_input}", color_in_use=color.GREEN, icon=CHECKMARK_ICON
                )
            return user_input
        elif default is not None:
            if post_user_input_message:
                value = "REDACTED" if redact_default else default
                self._overwrite_previous_line(
                    message=f"{post_user_input_message}{value}", color_in_use=color.GREEN, icon=CHECKMARK_ICON
                )
            return default

        return ""

    def _prompt_user_selection(self, message: str, options: List[Any]) -> Any:
        if self._dry_run:
            logger.debug(f"{message}: Dry-run mode.")
            return None

        if not options or len(options) == 0:
            logger.warning("Not sufficient options to prompt for user selection.")
            return None

        enriched_msg = f"{message}"
        inq_opts = []
        idx = 0
        # Add numbering to the list of options:
        #  1. Item-01
        #  2. Item-02
        #  3. Cancel
        for idx in range(len(options)):
            option = options[idx]
            inq_opts.insert(idx, f"{idx + 1 }. {option}")
            idx += 1
        inq_opts.insert(idx, f"{idx + 1}. Cancel")
        questions = [inquirer.List("selection", message=enriched_msg, choices=inq_opts)]
        inq_selection = inquirer.prompt(questions, theme=GreenPassion())

        result = None
        if "Cancel" in inq_selection["selection"]:
            return result

        for opt in options:
            # Find the original option without the numbering prefix
            if str(opt) in str(inq_selection):
                result = opt

        # Clear stdout selection lines:
        #   - Title line
        #   - Selectable lines
        #   - Cancel line
        lines_number = len(inq_opts) + 2
        self._clear_previous_line(lines_number)
        self._overwrite_previous_line(color_in_use=color.GREEN, message=f"Selected :: {result}", icon=CHECKMARK_ICON)

        return result

    def _prompt_user_multi_selection(self, message: str, options: List[Any]) -> Any:
        if self._dry_run:
            logger.debug(f"{message}: Dry-run mode.")
            return []

        if not options or len(options) == 0:
            logger.warning("Not sufficient options to prompt for user selection.")
            return None

        enriched_msg = f"{message} (space to select)"
        # Multi selection should not have numbering prefixes
        questions = [inquirer.Checkbox("selection", message=enriched_msg, choices=options)]
        inq_selection = inquirer.prompt(questions, theme=GreenPassion())
        if not inq_selection:
            return None
        result = inq_selection["selection"]

        # Clear stdout selection lines:
        #   - Title line
        #   - Selectable lines
        lines_number = len(options) + 2
        self._clear_previous_line(lines_number)
        self._overwrite_previous_line(color_in_use=color.GREEN, message=f"Selected :: {str(result)}", icon=CHECKMARK_ICON)
        return result

    def _prompt_yes_no(
        self,
        message: str,
        level: Optional[PromptLevel] = PromptLevel.HIGHLIGHT,
        post_yes_message: Optional[str] = None,
        post_no_message: Optional[str] = None,
    ) -> bool:

        if self._dry_run:
            logger.debug(f"{message}? (y/n): Dry-run mode.")
            return True

        if self._auto_prompt:
            logger.debug(f"{message}? (y/n): Auto-prompt mode.")
            return True

        color_in_use = self._get_color_from_prompt_level(level)
        prompt = f"{color_in_use}{message}? (y/n): {color.NONE}"
        user_input = input(prompt)
        if user_input == "" or user_input not in ["y", "n"]:
            self._clear_previous_line(count=2)
            self._prompt_yes_no(message=message, level=level)

        # TODO: Strip potential whitespaces such as newlines before hitting 'y'
        is_approved = user_input and user_input == "y"

        if is_approved:
            if post_yes_message:
                self._overwrite_previous_line(message=post_yes_message, color_in_use=color.GREEN, icon=CHECKMARK_ICON)
        else:
            if post_no_message:
                self._overwrite_previous_line(
                    message=post_no_message, color_in_use=color.BRIGHT_BLACK, icon=CROSSMARK_ICON
                )

        return is_approved

    def _prompt_for_enter(self, level: Optional[PromptLevel] = PromptLevel.INFO) -> bool:
        if self._dry_run:
            logger.debug("Press ENTER to continue...: Dry-run mode.")
            return True

        if self._auto_prompt:
            logger.debug("Press ENTER to continue...: Auto-prompt mode.")
            return True

        color_in_use = self._get_color_from_prompt_level(level)
        prompt = f"{color_in_use}  Press ENTER to continue...{color.NONE}"
        user_input = input(prompt)
        # Empty input means an Enter was pressed
        enter_pressed = not user_input
        if enter_pressed:
            self._clear_previous_line(count=2)
        return enter_pressed

    prompt_user_multi_selection_fn = _prompt_user_multi_selection
    prompt_user_selection_fn = _prompt_user_selection
    prompt_user_input_fn = _prompt_user_input
    prompt_yes_no_fn = _prompt_yes_no
    prompt_for_enter_fn = _prompt_for_enter
