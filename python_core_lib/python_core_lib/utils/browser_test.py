#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.utils.browser import open_browser


class BrowserTestShould(unittest.TestCase):
    @mock.patch("webbrowser.open")
    def test_os_arch_pair_linux(self, open_call: mock.MagicMock):
        url = "https://test.url.com"
        open_browser(url=url)
        open_call_kwargs = open_call.call_args.kwargs
        self.assertEqual(url, open_call_kwargs["url"])
