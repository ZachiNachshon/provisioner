#!/usr/bin/env python3

import json
from abc import abstractmethod

from provisioner.errors.cli_errors import FailedToSerializeConfiguration


class SerializationBase:

    dict_obj: dict

    @abstractmethod
    def __init__(self, dict_obj: dict) -> None:
        self.dict_obj = dict_obj
        # print the actual class name
        try:
            # print(f"Creating {self.__class__.__name__} with dict_obj: {dict_obj}")
            self._try_parse_config(dict_obj)
        except Exception as ex:
            raise FailedToSerializeConfiguration(f"Failed to serialize configuration. ex: {ex}")

    @abstractmethod
    def _try_parse_config(self, dict_obj: dict):
        pass

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @abstractmethod
    def merge(self, other: "SerializationBase") -> "SerializationBase":
        """
        Merge this serialization class with another
        """
        return self
