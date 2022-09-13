#!/usr/bin/env python3

from shutil import which
from loguru import logger
from ..errors.cli_errors import MissingUtilityException


class Checks:
    
    @staticmethod
    def create() -> "Checks":
        logger.debug("Creating checks validator...")
        return Checks()

    def __init__(self):
        pass

    def _is_tool_exist(self, name: str) -> bool:
        return which(name) is not None

    def _check_tool(self, name: str) -> None:
        if which(name) is None:
            raise MissingUtilityException(f"missing CLI tool. name: {name}")

    is_tool_exist_fn = _is_tool_exist
    check_tool_fn = _check_tool
