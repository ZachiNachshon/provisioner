#!/usr/bin/env python3

import io
import json
from os.path import expandvars
from typing import Any

from loguru import logger

from ..domain.serialize import SerializationBase
from ..infra.context import Context
from .io_utils import IOUtils


class JsonUtil:

    _verbose: bool
    io_utils: IOUtils

    def __init__(self, io_utils: IOUtils, verbose: bool) -> None:
        self.io_utils = io_utils
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils) -> "JsonUtil":
        logger.debug("Creating JSON util...")
        verbose = ctx.is_verbose()
        reader = JsonUtil(io_utils, verbose)
        return reader

    def _validate_json_file_path(self, file_path: str):
        if not self.io_utils.file_exists_fn(file_path):
            raise FileNotFoundError("Cannot find JSON file. path: {}".format(file_path))

    def _read_string(self, json_str: str, class_name: SerializationBase) -> SerializationBase:
        json_str_expanded = expandvars(json_str)
        json_data_dict = json.loads(json_str_expanded)
        if self._verbose:
            json_data_str = json.dumps(json_data_dict, indent=2)
            logger.debug(json_data_str)
        return class_name(json_data_dict)

    def _read_file(self, file_path: str, class_name: SerializationBase) -> SerializationBase:
        self._validate_json_file_path(file_path)
        with io.open(file_path, "r") as stream:
            json_data = json.load(stream)
            json_data_str = json.dumps(json_data, indent=2)
            if self._verbose:
                logger.debug(json_data_str)

            json_data_expanded = expandvars(json_data_str)
            json_dict_expanded = json.loads(json_data_expanded)
            return class_name(json_dict_expanded)

    def _to_json(self, obj: Any) -> str:
        if hasattr(obj, "__dict__"):
            return json.dumps(obj.__dict__, default=vars, indent=2)
        else:
            return json.dumps(obj, default=vars, indent=2)

    read_file_fn = _read_file
    read_string_fn = _read_string
    to_json_fn = _to_json
