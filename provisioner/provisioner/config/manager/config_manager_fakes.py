# #!/usr/bin/env python3


# from typing import Any
# from provisioner.config.manager.config_manager import ConfigManager

# from provisioner.domain.serialize import SerializationBase

# class FakeConfigManager(ConfigManager):

#     # Static variable
#     config: SerializationBase = None

#     def __init__(self, yaml_util: YamlUtil):
#         super().__init__(yaml_util=yaml_util)

#     @staticmethod
#     def _create_fake(yaml_util: YamlUtil) -> "FakeConfigReader":
#         fake_config_reader = FakeConfigReader(yaml_util=yaml_util)
#         fake_config_reader.read_config_fn = (
#             lambda internal_path, class_name, user_path: fake_config_reader._config_selector(user_path, internal_path)
#         )
#         return fake_config_reader

#     @staticmethod
#     def create(yaml_util: YamlUtil) -> "FakeConfigReader":
#         return FakeConfigReader._create_fake(yaml_util=yaml_util)

#     @staticmethod
#     def load(config: SerializationBase) -> None:

#     def get_config() -> Any:
#         return FakeConfigResolver.config
