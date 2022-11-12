#!/usr/bin/env python3

from ..domain.serialize import SerializationBase
from ..utils.yaml_util import YamlUtil
from .config_reader import ConfigReader


class FakeConfigReader(ConfigReader):

    registered_internal_config_path_to_object: dict[str, SerializationBase] = {}
    registered_user_config_path_to_object: dict[str, SerializationBase] = {}

    def __init__(self, yaml_util: YamlUtil):
        super().__init__(yaml_util=yaml_util)

    @staticmethod
    def _create_fake(yaml_util: YamlUtil) -> "FakeConfigReader":
        fake_config_reader = FakeConfigReader(yaml_util=yaml_util)
        fake_config_reader.read_config_fn = (
            lambda internal_path, class_name, user_path: fake_config_reader._config_selector(user_path, internal_path)
        )
        return fake_config_reader

    @staticmethod
    def create(yaml_util: YamlUtil) -> "FakeConfigReader":
        return FakeConfigReader._create_fake(yaml_util=yaml_util)

    def register_user_path_config(self, path: str, class_obj: SerializationBase):
        self.registered_user_config_path_to_object[path] = class_obj

    def register_internal_path_config(self, path: str, class_obj: SerializationBase):
        self.registered_internal_config_path_to_object[path] = class_obj

    def _config_selector(self, user_path: str, internal_path: str) -> SerializationBase:
        if user_path:
            if user_path in self.registered_user_config_path_to_object:
                return self.registered_user_config_path_to_object.get(user_path)

        if internal_path:
            if internal_path in self.registered_internal_config_path_to_object:
                return self.registered_internal_config_path_to_object.get(internal_path)

        raise LookupError(f"Fake config reader is missing user-path and/or internal-path, cannot mock")
