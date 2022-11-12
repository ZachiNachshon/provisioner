#!/usr/bin/env python3

from configparser import ConfigParser, Error
from os.path import expandvars
from typing import List, Optional

from loguru import logger

from ..errors.cli_errors import MissingPropertiesFileKey
from ..utils.io_utils import IOUtils


class Patterns:

    io: IOUtils
    config_parser: ConfigParser = None

    """
    Config parser requires that the properties file will have a fake head section i.e. [Something]
    It is becuase this library used to read *.ini files.
    We're faking it so the user won't have to add such redunadant header
    """
    fake_section_name: str = "FAKE_SECTION_NAME"

    @staticmethod
    def create(io_utils: IOUtils) -> "Patterns":
        logger.debug("Creating a patterns reader...")
        props = Patterns(io_utils, ConfigParser())
        return props

    def __init__(self, io_utils: IOUtils, config_parser: ConfigParser) -> None:
        self.io = io_utils
        self.config_parser = config_parser

    def _resolve_pattern(self, path: str, key: str, *args) -> str:
        if not self.io.file_exists_fn(path):
            err_msg = "Cannot find patterns file. path: {}".format(path)
            logger.warning(err_msg)
            raise FileNotFoundError(err_msg)

        patterns_output = self.io.read_file_safe_fn(path)

        # Config parser can read only if a section header exists i.e.
        # [FAKE_SECTION_NAME]
        # prop_key=prop_value
        patterns_output = "[{}]\n{}".format(self.fake_section_name, patterns_output)
        value = None
        try:
            self.config_parser.read_string(patterns_output)
            value = self.config_parser.get(self.fake_section_name, key)
        except Exception as ex:
            pass

        if value:
            logger.debug("Read patterns key successfully. key: {}, value: {}".format(key, value))
            value = value.format(args)
            return expandvars(value)

        raise MissingPropertiesFileKey("missing key in patterns file. key: {}, path: {}".format(key, path))

    resolve_pattern_fn = _resolve_pattern
