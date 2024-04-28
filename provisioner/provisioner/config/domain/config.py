#!/usr/bin/env python3

from typing import Any, List

from loguru import logger
from provisioner.domain.serialize import SerializationBase


class ProvisionerConfig(SerializationBase):
    """
    Configuration structure -

    provisioner:
        plugins_definitions: 
        - name: "Installers Plugin",
            description: "Install anything anywhere on any OS/Arch either on a local or remote machine.",
            author: "Zachi Nachshon",
            maintainer: "ZachiNachshon"
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if not dict_obj:
            return 
        if "provisioner" in dict_obj:
            provisioner_data = dict_obj["provisioner"]
            if "plugins_definitions" in provisioner_data:
                self._parse_plugins_definitions_block(provisioner_data["plugins_definitions"])

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        # Provisioner config is internal only and shouldn't get merged from user config
        return self

    def _parse_plugins_definitions_block(self, plugins_defs_block: dict):
        self.plugins_definitions = {}
        for definition in plugins_defs_block:
            def_obj = self.PluginDefinition()
            if "package_name" in definition:
                def_obj.package_name = definition["package_name"]
            else:
                logger.warning(f"Plugin definition is missing a package_name. Skipping definition.")
                continue
            if "name" in definition:
                def_obj.name = definition["name"]
            if "description" in definition:
                def_obj.description = definition["description"]
            if "author" in definition:
                def_obj.author = definition["author"]
            if "maintainer" in definition:
                def_obj.maintainer = definition["maintainer"]
            self.plugins_definitions[def_obj.package_name] = def_obj

    class PluginDefinition:
        name: str
        description: str
        author: str
        maintainer: str
        package_name: str

        def __init__(
                self, 
                name: str = None, 
                description: str = None, 
                author: str = None, 
                maintainer: str = None,
                package_name: str = None) -> None:
            
            self.name = name
            self.description = description
            self.author = author
            self.maintainer = maintainer
            self.package_name = package_name

    plugins_definitions: dict[str, PluginDefinition] = []
    plugins: dict[str, Any] = {}
