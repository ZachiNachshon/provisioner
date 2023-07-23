#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.test_lib.assertions import Assertion

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.anchor.typer_anchor_opts_fakes import TestDataAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts

ARG_CONFIG_INTERNAL_PATH = "/path/to/internal/config"
ARG_CONFIG_USER_PATH = "/path/to/user/config"

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_features_lib/config/config_resolver_test.py
#


class FakeTestConfig(SerializationBase):

    remote: RemoteConfig = None
    anchor: AnchorConfig = None

    def __init__(self, remote_config: RemoteConfig, anchor_config: AnchorConfig) -> None:
        super().__init__({})
        self.remote = remote_config
        self.anchor = anchor_config

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self


class ConfigResolverTestShould(unittest.TestCase):
    @staticmethod
    def create_fake_config():
        return FakeTestConfig(
            remote_config=TestDataRemoteOpts.create_fake_remote_opts().remote_config,
            anchor_config=TestDataAnchorOpts.create_fake_anchor_opts().anchor_config,
        )

    @mock.patch("python_core_lib.config.config_reader.ConfigReader.read_config_fn", side_effect=[create_fake_config()])
    def test_set_typer_anchor_opts_from_config_values(self, run_call: mock.MagicMock) -> None:
        ConfigResolver.load(
            internal_path=ARG_CONFIG_INTERNAL_PATH, user_path=ARG_CONFIG_USER_PATH, class_name=FakeTestConfig
        )
        resolved_config = ConfigResolver.get_config()
        Assertion.expect_equal_objects(self, resolved_config.anchor, TyperAnchorOpts.anchor_config)
        Assertion.expect_equal_objects(self, resolved_config.remote, TyperRemoteOpts.remote_config)
