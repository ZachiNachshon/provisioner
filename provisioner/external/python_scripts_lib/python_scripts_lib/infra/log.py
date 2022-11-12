#!/usr/bin/env python3

import logging
import sys

from loguru import logger

ABBREVIATE_CHARS_THRESHOLD = 30


def _set_log_level_names_format(level_filter, dry_run: bool = False):
    # Remove default logger
    logger.remove()

    # h = logging.StreamHandler()
    # f = AbbreviationFormatter('%(name)-6s %(message)s')
    # h.setFormatter(f)

    if level_filter.level == "DEBUG":
        # debug_fmt = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        debug_fmt = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level>: <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        if dry_run:
            debug_fmt = "<level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level><white>{message}</white></level>"
            debug_fmt = "<b><magenta>[DRY-RUN]</magenta></b> | " + debug_fmt

        logger.add(
            sys.stdout,
            level="DEBUG",
            format=debug_fmt,
            filter=level_filter,
            colorize=True,
            serialize=False,
            backtrace=False,
            diagnose=True,
            enqueue=False,
            catch=True,
        )
    else:
        fmt = "<level>{level}</level>: <level><white>{message}</white></level>"
        if dry_run:
            fmt = "<b><magenta>[DRY-RUN]</magenta></b> " + fmt

        logger.add(
            sys.stdout,
            level="INFO",
            format=fmt,
            filter=level_filter,
            colorize=True,
            serialize=False,
            backtrace=False,
            diagnose=True,
            enqueue=False,
            catch=True,
        )


class AbbreviationFormatter(logging.Formatter):
    def format(self, record):
        saved_name = record.name  # save and restore for other formatters if desired
        parts = saved_name.split(".")
        # import pdb; pdb.set_trace()
        record.name = ".".join(p[0] for p in parts)
        result = super().format(record)
        record.name = saved_name
        return result


class LoggerManager:
    def initialize(self, verbose: bool = False, dry_run: bool = False):
        try:
            level_filter = LevelFilter("DEBUG") if verbose else LevelFilter("INFO")
            _set_log_level_names_format(level_filter, dry_run)

            # logger.debug("This is a debug message")
            # logger.info("This is a info message")
            # logger.success("This is a success message")
            # logger.warning("This is a warning message")
            # logger.error("This is a error message")
            # logger.critical("This is a critical message")

        except Exception as err:
            print("Logger failed to initialize. error: " + str(err))


class LevelFilter:
    def __init__(self, level: str):
        self.level = level

    def abbreviate(self, package_name: str) -> str:
        """
        Printing logs shorten packages
        Example:
          | DEBUG   | e.p.u.prompter:_prompt_user_input:32 - message...
        """
        parts = package_name.split(".")
        if len(parts) <= 1:
            return package_name
        last = parts[len(parts) - 1]
        result = ""
        for p in parts:
            if p == last:
                result += f"{last}"
            else:
                result += f"{p[0]}."
        return result

    def __call__(self, record):
        levelno = logger.level(self.level).no
        should_log = record["level"].no >= levelno
        if should_log and len(record["name"]) > ABBREVIATE_CHARS_THRESHOLD:
            record["name"] = self.abbreviate(record["name"])
        return should_log

        # levelno = logger.level(self.level).no
        # return record["level"].no >= levelno
