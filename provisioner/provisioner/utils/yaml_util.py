#!/usr/bin/env python3

import io
import json
from os.path import expandvars
from typing import Any

import yaml
from loguru import logger

from provisioner.domain.serialize import SerializationBase
from provisioner.infra.context import Context
from provisioner.utils.io_utils import IOUtils


class YamlUtil:

    _verbose: bool
    io_utils: IOUtils

    def __init__(self, io_utils: IOUtils, verbose: bool) -> None:
        self.io_utils = io_utils
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils) -> "YamlUtil":
        logger.debug("Creating YAML util...")
        verbose = ctx.is_verbose()
        reader = YamlUtil(io_utils, verbose)
        return reader

    def _validate_yaml_file_path(self, file_path: str):
        if not self.io_utils.file_exists_fn(file_path):
            raise FileNotFoundError("Cannot find YAML file. path: {}".format(file_path))

    # def _write_to_file(self, file_path: str, yaml_text: str) -> bool:
    #     success = True
    #     self._validate_yaml_file_path(file_path)
    #     try:
    #         with io.open(file_path, 'w', encoding='utf8') as outfile:
    #             yaml.dump(yaml_text, outfile, default_flow_style=False, allow_unicode=True)
    #     except Exception as ex:
    #         logger.error(f"Failed to write to YAML file. ex: {str(ex)}")
    #         success = False

    #     return success

    def _read_string(self, yaml_str: str, cls: SerializationBase) -> SerializationBase:
        yaml_str_expanded = expandvars(yaml_str)
        json_data_list_of_dicts = yaml.safe_load(yaml_str_expanded)
        if self._verbose:
            json_data_str = json.dumps(json_data_list_of_dicts, indent=2)
            logger.debug(json_data_str)
        return cls(json_data_list_of_dicts)

    def _read_file_as_json_dict(self, file_path: str) -> dict:
        self._validate_yaml_file_path(file_path)
        with io.open(file_path, "r") as stream:
            json_data = yaml.safe_load(stream)
            json_data_str = json.dumps(json_data, indent=2)
            if self._verbose:
                logger.debug(json_data_str)
            json_data_expanded = expandvars(json_data_str)
            json_dict_expanded = json.loads(json_data_expanded)
            return json_dict_expanded

    def _read_file(self, file_path: str, cls: SerializationBase) -> SerializationBase:
        json_data_str = self._read_file_as_json_dict(file_path=file_path)
        try:
            res = cls(json_data_str)
            return res
        except Exception as ex:
            msg = f"Failed to read file as JSON. path: {file_path}, ex: {str(ex)}"
            print(msg)
            logger.error(msg)
        return None

    def _json_to_yaml(self, json_str: str) -> str:
        # Convert JSON string to dictionary
        dict_obj = json.loads(json_str)
        # Convert dictionary to YAML string
        return yaml.dump(dict_obj)
    
    read_file_as_json_dict_fn = _read_file_as_json_dict
    read_file_fn = _read_file
    read_string_fn = _read_string
    json_to_yaml_fn = _json_to_yaml