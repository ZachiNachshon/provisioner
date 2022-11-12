#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from ..domain.serialize import SerializationBase
from ..errors.cli_errors import FailedToReadConfigurationFile
from ..utils.yaml_util import YamlUtil


class ConfigReader:

    yaml_util: YamlUtil

    def __init__(self, yaml_util: YamlUtil) -> None:
        self.yaml_util = yaml_util

    @staticmethod
    def create(yaml_util: YamlUtil) -> "ConfigReader":
        logger.debug("Creating config reader...")
        reader = ConfigReader(yaml_util)
        return reader

    def _safe_read_config_path(self, path: str, class_name: SerializationBase) -> SerializationBase:
        try:
            config = self.yaml_util.read_file_fn(file_path=path, class_name=class_name)
            return config
        except Exception as ex:
            logger.debug(f"Config file does not exists for safe read. path {path}")
        return None

    def _try_read_config_path(self, path: str, class_name: SerializationBase) -> SerializationBase:
        config = self.yaml_util.read_file_fn(file_path=path, class_name=class_name)
        return config

    def _merge_user_config_with_internal(
        self, internal_config: SerializationBase, user_config: SerializationBase
    ) -> SerializationBase:
        try:
            merged_config = internal_config.merge(user_config)
            return merged_config
        except Exception as ex:
            logger.error(f"Failed to merge user and internal configurations. ex: {ex}")
        return None

    def _read_config(
        self, internal_path: str, class_name: SerializationBase, user_path: Optional[str] = None
    ) -> SerializationBase:
        """
        Read mandatory internal configuration.
        Try to read user configuration, if exists merge with internal and return.
        When no user configuration is found, return internal configuration.
        """
        logger.debug("Reading internal config")
        internal_config = self._try_read_config_path(path=internal_path, class_name=class_name)
        if not user_path:
            return internal_config

        logger.debug("Try reading user config")
        user_config = self._safe_read_config_path(path=user_path, class_name=class_name)
        if user_config == None:
            logger.debug(f"Could not find or serialize user config")
            return internal_config
        else:
            merged_config = self._merge_user_config_with_internal(
                internal_config=internal_config, user_config=user_config
            )
            if merged_config == None:
                raise FailedToReadConfigurationFile("Failed to merge user and internal configuration.")
            return merged_config

    read_config_fn = _read_config
