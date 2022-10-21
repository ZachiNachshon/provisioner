#!/usr/bin/env python3

from loguru import logger

from external.python_scripts_lib.python_scripts_lib.config.config_reader import (
    ConfigReader,
)
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliGlobalArgsNotInitialized,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.yaml_util import YamlUtil
from rpi.os.domain.config import ProvisionerConfig


class ConfigResolver:

    config_reader: ConfigReader
    _internal_path: str
    _user_path: str

    # Static variable
    config: ProvisionerConfig

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
    def resolve(internal_path: str, user_path: str) -> None:
        logger.debug("Loading configuration...")
        empty_ctx = Context.create()
        resolver = ConfigResolver._create(empty_ctx, internal_path, user_path)
        ConfigResolver.config = resolver.config_reader.read_config_fn(
            internal_path=internal_path, class_name=ProvisionerConfig, user_path=user_path
        )

    def get_config() -> ProvisionerConfig:
        if not ConfigResolver.config:
            raise CliGlobalArgsNotInitialized("Trying to read configuration before loading")
        return ConfigResolver.config
