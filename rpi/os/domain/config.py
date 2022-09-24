#!/usr/bin/env python3

from external.python_scripts_lib.python_scripts_lib.domain.serialize  import SerializationBase

class ProvisionerConfig(SerializationBase):

    active_system: str
    download_url_32bit: str
    download_url_64bit: str

    def __init__(self, dict_obj) -> None:
        raspbian_config = dict_obj["provisioner"]["rpi"]["os"]["raspbian"]
        self.active_system = raspbian_config["activeSystem"]
        self.download_url_32bit = raspbian_config["32bit"]["downloadUrl"]
        self.download_url_64bit = raspbian_config["64bit"]["downloadUrl"]

    def get_os_raspbian_download_url(self):
        if self.active_system == "64bit":
            return self.download_url_64bit
        return self.download_url_32bit
