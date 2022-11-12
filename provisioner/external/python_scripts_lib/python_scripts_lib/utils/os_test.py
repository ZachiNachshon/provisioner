#!/usr/bin/env python3

import unittest
from dataclasses import dataclass
from unittest import mock

from ..utils.os import OsArch


class OsArchTestShould(unittest.TestCase):
    @dataclass
    class uname_result_mock:
        system: str = ""
        machine: str = ""
        release: str = ""

    @mock.patch("platform.uname", side_effect=[uname_result_mock(system="Linux", machine="AMD64", release="test_rls")])
    def test_os_arch_pair_linux(self, uname_call: mock.MagicMock):
        os_arch = OsArch()
        pair = os_arch.as_pair()
        self.assertEqual(pair, "linux_amd64")
        self.assertTrue(os_arch.is_linux())

    @mock.patch("platform.uname", side_effect=[uname_result_mock(system="Darwin", machine="AMD64", release="test_rls")])
    def test_os_arch_pair_darwin(self, uname_call: mock.MagicMock):
        os_arch = OsArch()
        pair = os_arch.as_pair()
        self.assertEqual(pair, "darwin_amd64")
        self.assertTrue(os_arch.is_darwin())

    @mock.patch("platform.uname", side_effect=[uname_result_mock(system="Windows", machine="ARM", release="test_rls")])
    def test_os_arch_pair_windows(self, uname_call: mock.MagicMock):
        os_arch = OsArch()
        pair = os_arch.as_pair()
        self.assertEqual(pair, "windows_arm")
        self.assertTrue(os_arch.is_windows())

    @mock.patch(
        "platform.uname", side_effect=[uname_result_mock(system="Darwin", machine="x86_64", release="test_rls")]
    )
    def test_os_arch_pair_with_mapping(self, uname_call: mock.MagicMock):
        os_arch = OsArch()
        pair = os_arch.as_pair(mapping={"x86_64": "amd64"})
        self.assertEqual(pair, "darwin_amd64")
