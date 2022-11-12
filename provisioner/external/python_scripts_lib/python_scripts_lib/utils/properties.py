#!/usr/bin/env python3

from configparser import ConfigParser
from typing import Optional

from loguru import logger

from ..errors.cli_errors import MissingPropertiesFileKey
from ..utils.io_utils import IOUtils


class Properties:

    io: IOUtils
    config_parser: ConfigParser = None

    """
    Config parser requires that the properties file will have a fake head section i.e. [Something]
    It is becuase this library used to read *.ini files.
    We're faking it so the user won't have to add such redunadant header
    """
    fake_section_name: str = "FAKE_SECTION_NAME"

    @staticmethod
    def create(io_utils: IOUtils) -> "Properties":
        logger.debug("Creating a properties reader...")
        props = Properties(io_utils, ConfigParser())
        return props

    def __init__(self, io_utils: IOUtils, config_parser: ConfigParser) -> None:
        self.io = io_utils
        self.config_parser = config_parser

    def _read_value(self, path: str, key: str, default: Optional[str] = None) -> str:
        if not self.io.file_exists_fn(path):
            err_msg = "Cannot find properties file. path: {}".format(path)
            logger.warning(err_msg)
            raise FileNotFoundError(err_msg)

        props_output = self.io.read_file_safe_fn(path)

        # Config parser can read only if a section header exists i.e.
        # [FAKE_SECTION_NAME]
        # prop_key=prop_value
        props_output = "[{}]\n{}".format(self.fake_section_name, props_output)
        value = None
        try:
            self.config_parser.read_string(props_output)
            value = self.config_parser.get(self.fake_section_name, key)
        except Exception as ex:
            pass

        if value:
            logger.debug("Read property key successfully. key: {}, value: {}".format(key, value))
            return value
        elif default:
            logger.debug("Return default value for key. key: {}, default: {}, path: {}".format(key, default, path))
            return default

        raise MissingPropertiesFileKey("missing key in properties file. key: {}, path: {}".format(key, path))

    read_value_fn = _read_value
