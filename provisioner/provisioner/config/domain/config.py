#!/usr/bin/env python3

from typing import Any
from provisioner.domain.serialize import SerializationBase

class ProvisionerConfig(SerializationBase):
    
    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        # provisioner_data = dict_obj["provisioner"]
        # No specific configurations for the provisioner itself
        pass

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        # No specific configurations for the provisioner itself
        return self
    
    plugins: dict[str, Any] = {}