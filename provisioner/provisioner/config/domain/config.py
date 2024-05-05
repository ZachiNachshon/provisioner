#!/usr/bin/env python3

from typing import Any

from loguru import logger
from provisioner.domain.serialize import SerializationBase

"""
Configuration structure -

provisioner:
    plugins_definitions: 
    - name: "Installers Plugin",
        description: "Install anything anywhere on any OS/Arch either on a local or remote machine.",
        author: "Zachi Nachshon",
        maintainer: "ZachiNachshon"
"""    

class PluginDefinition(SerializationBase):
    name: str
    description: str
    author: str
    maintainer: str
    package_name: str

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)    

    def _try_parse_config(self, dict_obj: dict):
        if "package_name" in dict_obj:
            self.package_name = dict_obj["package_name"]
        else:
            logger.warning(f"Invalid plugin definition, missing a package_name. Plugin will not load.")
            return
        if "name" in dict_obj:
            self.name = dict_obj["name"]
        if "description" in dict_obj:
            self.description = dict_obj["description"]
        if "author" in dict_obj:
            self.author = dict_obj["author"]
        if "maintainer" in dict_obj:
            self.maintainer = dict_obj["maintainer"]

    def merge(self, other: "ProvisionerConfig.PluginDefinition") -> SerializationBase:
        # Provisioner definitions config is internal only and shouldn't get merged from user config
        return self
        
class ProvisionerConfig(SerializationBase):
    plugins_definitions: dict[str, PluginDefinition] = {}
    plugins: dict[str, Any] = {}

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "plugins_definitions" in dict_obj:
            definitions = dict_obj["plugins_definitions"]
            for definition in definitions:
                def_obj = PluginDefinition(definition)
                self.plugins_definitions[def_obj.package_name] = def_obj

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        # Provisioner config is internal only and shouldn't get merged from user config
        return self

