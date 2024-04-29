#!/usr/bin/env python3


from loguru import logger

from provisioner.config.reader.config_reader import ConfigReader
from provisioner.domain.serialize import SerializationBase
from provisioner.errors.cli_errors import FailedToMergeConfiguration, FailedToReadConfigurationFile
from provisioner.infra.context import Context
from provisioner.utils.io_utils import IOUtils
from provisioner.utils.yaml_util import YamlUtil


class ConfigManager:

    _config_reader: ConfigReader
    _instance: "ConfigManager" = None

    config: SerializationBase = None
    # This is the user config YAML file as json string which is located on ~/.config/provisioner/config.yaml
    _user_config_raw_dict: dict = None

    def __init__(self, ctx: Context) -> None:
        io = IOUtils.create(ctx)
        yaml_util = YamlUtil.create(ctx, io)
        self._config_reader = ConfigReader.create(yaml_util)

    @staticmethod
    def nullify() -> None:
        if ConfigManager._instance is not None:
            ConfigManager.instance()._user_config_raw_dict = None
            ConfigManager.instance().config = None

    @staticmethod
    def instance() -> "ConfigManager":
        if ConfigManager._instance is None:
            logger.debug("Creating ConfigManager...")
            ConfigManager._instance = ConfigManager(ctx=Context.create())
        return ConfigManager._instance

    def load(self, internal_path: str, user_path: str, cls: SerializationBase) -> None:
        logger.debug(f"Loading internal provisioner configuration. path: {internal_path}")
        # Read provisioner internal configuration
        internal_cfg_obj = self._config_reader.read_config_safe_fn(path=internal_path, cls=cls)
        if internal_cfg_obj is None:
            raise FailedToReadConfigurationFile(
                f"Failed to read internal provisioner configuration. path: {internal_path}"
            )

        # When no user configuration is found, return internal configuration.
        if user_path is None:
            self.config = internal_cfg_obj
            return

        # Cache user configuration as json string to prevent redundant file reads
        if self._user_config_raw_dict is None:
            logger.debug("Reading user provisioner configuration")
            # User might not have a configuration file, so the _user_config_raw_dict will be None
            self._user_config_raw_dict = self._config_reader.read_config_as_json_dict_safe_fn(path=user_path)

        logger.debug("Merging user and internal provisioner configuration")
        self.config = self._merge_user_config_with_internal(
            internal_config=internal_cfg_obj, user_config=cls(self._user_config_raw_dict)
        )
        if self.config is None:
            raise FailedToMergeConfiguration("Failed to merge user and internal provisioner configuration.")

    def load_plugin_config(self, plugin_name: str, internal_path: str, cls: SerializationBase) -> None:
        logger.debug(f"Loading internal plugin configuration. name: {plugin_name}")
        # Read plugin internal configuration
        internal_plgn_cfg_obj = self._config_reader.read_config_safe_fn(path=internal_path, cls=cls)
        if internal_plgn_cfg_obj is None:
            raise FailedToReadConfigurationFile(f"Failed to read internal plugin configuration. name: {plugin_name}")

        # For cases there config is empty
        if self.config.dict_obj is None:
            self.config.dict_obj = {}

        # Config object was initialized by the load defintion
        if self.config.dict_obj.get("plugins") is None:
            # plugins attribute is a dict of type: dict[str, SerializationBase]
            self.config.dict_obj["plugins"] = {}

        # If there isn't any user configuration, return internal configuration
        if self._user_config_raw_dict is None:
            logger.debug("No user configuration could be found for provisioner")
            self.config.dict_obj["plugins"][plugin_name] = internal_plgn_cfg_obj
            return

        maybe_plugin_cfg_dict = self._user_config_raw_dict.get("plugins", {}).get(plugin_name)
        # If plugin user configuration is found, but is empty, return internal configuration
        if maybe_plugin_cfg_dict is None:
            logger.debug(f"No user configuration could be found for plugin. name: {plugin_name}")
            self.config.dict_obj["plugins"][plugin_name] = internal_plgn_cfg_obj
            return
        else:
            # If plugin user configuration is found, non empty, merge it with internal configuration
            logger.debug(f"Merging user and internal plugin configuration. name: {plugin_name}")
            merged_plgn_cfg_obj = self._merge_user_config_with_internal(
                internal_config=internal_plgn_cfg_obj, user_config=cls(maybe_plugin_cfg_dict)
            )
            self.config.dict_obj["plugins"][plugin_name] = merged_plgn_cfg_obj

    def _merge_user_config_with_internal(
        self, internal_config: SerializationBase, user_config: SerializationBase
    ) -> SerializationBase:
        try:
            merged_config = internal_config.merge(user_config)
            return merged_config
        except Exception as ex:
            print(f"Failed to merge user and internal configurations. cls: {type(internal_config).__name__}, ex: {ex}")
            logger.error(
                f"Failed to merge user and internal configurations. cls: {type(internal_config).__name__}, ex: {ex}"
            )
        return None

    def get_config(self) -> SerializationBase:
        return self.config

    def get_plugin_config(self, name: str) -> SerializationBase:
        return self.config.dict_obj["plugins"].get(name, {})
