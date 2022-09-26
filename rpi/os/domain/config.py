#!/usr/bin/env python3

from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import FailedToSerializeConfiguration
from external.python_scripts_lib.python_scripts_lib.domain.serialize import SerializationBase

class ProvisionerConfig(SerializationBase):

    active_system: str = None
    download_url_32bit: str = None
    download_url_64bit: str = None

    def __init__(self, dict_obj) -> None:
        super().__init__(dict_obj)
        try:
            self._try_parse_config()
        except Exception as ex:
            raise FailedToSerializeConfiguration(f"Falied to serialize configuration. ex: {ex}")

    def _try_parse_config(self):
        provisioner_data = self.dict_obj["provisioner"]
        if "rpi" in provisioner_data and "os" in provisioner_data["rpi"] and "raspbian" in provisioner_data["rpi"]["os"]:
            raspbian_config = provisioner_data["rpi"]["os"]["raspbian"]
            if "active_system" in raspbian_config: 
                self.active_system = raspbian_config["active_system"]
            if "32bit" in raspbian_config:
                self.download_url_32bit = raspbian_config["32bit"]["download_url"]
            if "64bit" in raspbian_config:
                self.download_url_64bit = raspbian_config["64bit"]["download_url"]

    def merge(self, other: "ProvisionerConfig") -> SerializationBase:
        if other.active_system:
            self.active_system = other.active_system

        if other.download_url_32bit:
            self.download_url_32bit = other.download_url_32bit

        if other.download_url_64bit:
            self.download_url_64bit = other.download_url_64bit

        return self

    def get_os_raspbian_download_url(self):
        if self.active_system == "64bit":
            return self.download_url_64bit
        return self.download_url_32bit
