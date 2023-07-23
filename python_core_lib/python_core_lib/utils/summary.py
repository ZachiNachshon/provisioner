#!/usr/bin/env python3

from typing import Any, Callable

from loguru import logger

from python_core_lib.infra.context import Context
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter


class Summary:

    _dry_run: bool = None
    _verbose: bool = None
    _auto_prompt: bool = None
    _json_util: JsonUtil = None
    _printer: Printer = None
    _prompter: Prompter = None
    _summary_dict: dict = {}

    def __init__(
        self, dry_run: bool, verbose: bool, auto_prompt: bool, json_util: JsonUtil, printer: Printer, prompter: Prompter
    ):

        self._dry_run = dry_run
        self._verbose = verbose
        self._auto_prompt = auto_prompt
        self._json_util = json_util
        self._printer = printer
        self._prompter = prompter

    @staticmethod
    def create(ctx: Context, json_util: JsonUtil, printer: Printer, prompter: Prompter) -> "Summary":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        auto_prompt = ctx.is_auto_prompt()
        logger.debug(f"Creating a summary generator (dry_run: {dry_run}, verbose: {verbose})...")
        return Summary(dry_run, verbose, auto_prompt, json_util, printer, prompter)

    def append(self, attribute_name: str, value: Any) -> "Summary":
        self._summary_dict[attribute_name] = value
        return self

    def append_result(self, attribute_name: str, call: Callable[[], str]) -> Any:
        result = call()
        self.append(attribute_name, result)
        return result

    def _get_text(self) -> str:
        result_dict = {}
        result_dict["summary"] = self._summary_dict
        return self._json_util.to_json_fn(result_dict)

    def show_summary_and_prompt_for_enter(self, title: str) -> None:
        self._printer.new_line_fn()
        self._printer.print_horizontal_line_fn(f"{title}")
        self._printer.print_fn(self._get_text())
        if not self._auto_prompt:
            self._printer.new_line_fn()
            self._prompter.prompt_for_enter_fn()
