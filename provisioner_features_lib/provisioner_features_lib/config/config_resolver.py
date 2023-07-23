#!/usr/bin/env python3

from typing import Any, Optional

from loguru import logger
from python_core_lib.config.config_reader import ConfigReader
from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.infra.context import Context
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.yaml_util import YamlUtil

from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts


class ConfigResolver:

    config_reader: ConfigReader
    _internal_path: str
    _user_path: str

    # Static variable
    config: SerializationBase = None

    def __init__(self, ctx: Context, internal_path: str, user_path: str) -> None:
        self._internal_path = internal_path
        self._user_path = user_path
        io = IOUtils.create(ctx)
        yaml_util = YamlUtil.create(ctx, io)
        self.config_reader = ConfigReader.create(yaml_util)

    @staticmethod
    def _create(ctx: Context, internal_path: str, user_path: str) -> "ConfigResolver":
        logger.debug("Creating typer cli config resolver...")
        resolver = ConfigResolver(ctx, internal_path, user_path)
        return resolver

    @staticmethod
    def load(internal_path: str, user_path: str, class_name: SerializationBase, debug: Optional[bool] = False) -> None:
        if not debug:
            logger.remove()

        logger.debug("Loading configuration...")
        empty_ctx = Context.create()
        resolver = ConfigResolver._create(empty_ctx, internal_path, user_path)
        ConfigResolver.config = resolver.config_reader.read_config_fn(
            internal_path=internal_path, class_name=class_name, user_path=user_path
        )
        TyperRemoteOpts.load(ConfigResolver.config.remote)
        TyperAnchorOpts.load(ConfigResolver.config.anchor)

    def get_config() -> Any:
        return ConfigResolver.config
