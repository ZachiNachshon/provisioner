#!/usr/bin/env python3

from loguru import logger

from provisioner.domain.serialize import SerializationBase
from provisioner.utils.yaml_util import YamlUtil


class ConfigReader:

    yaml_util: YamlUtil

    def __init__(self, yaml_util: YamlUtil) -> None:
        self.yaml_util = yaml_util

    @staticmethod
    def create(yaml_util: YamlUtil) -> "ConfigReader":
        logger.debug("Creating config reader...")
        reader = ConfigReader(yaml_util)
        return reader

    def _read_config_as_json_dict(self, path: str) -> dict:
        return self.yaml_util.read_file_as_json_dict_fn(file_path=path)

    def _read_config_as_json_dict_safe(self, path: str) -> dict:
        try:
            return self.yaml_util.read_file_as_json_dict_fn(file_path=path)
        except Exception as ex:
            logger.debug(f"Failed reading config file as JSON. path {path}, ex: {ex}")
        return None

    def _read_config(self, internal_path: str, cls: SerializationBase) -> SerializationBase:
        return self.yaml_util.read_file_fn(file_path=internal_path, cls=cls)

    def _read_config_safe(self, path: str, cls: SerializationBase) -> SerializationBase:
        try:
            config = self._read_config(path, cls)
            return config
        except Exception as ex:
            print(f"Failed reading config file. path {path}, ex: {ex}")
        return None

    read_config_as_json_dict_fn = _read_config_as_json_dict
    read_config_as_json_dict_safe_fn = _read_config_as_json_dict_safe
    read_config_fn = _read_config
    read_config_safe_fn = _read_config_safe
