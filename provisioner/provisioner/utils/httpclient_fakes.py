#!/usr/bin/env python3

from typing import Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.httpclient import HttpClient


class FakeHttpClient(TestFakes, HttpClient):
    def __init__(self, dry_run: bool, verbose: bool):
        TestFakes.__init__(self)
        HttpClient.__init__(
            self, io_utils=None, progress_indicator=None, printer=None, dry_run=dry_run, verbose=verbose
        )

    @staticmethod
    def create(ctx: Context) -> "FakeHttpClient":
        fake = FakeHttpClient(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
        fake.get_fn = MagicMock(side_effect=fake.get_fn)
        fake.head_fn = MagicMock(side_effect=fake.head_fn)
        fake.post_fn = MagicMock(side_effect=fake.post_fn)
        fake.download_file_fn = MagicMock(side_effect=fake.download_file_fn)
        return fake

    def get_fn(self, url: str, timeout: int = 30, headers: Optional[dict[str, str]] = None) -> bool:
        return self.trigger_side_effect("get_fn", url, timeout, headers)

    def head_fn(self, url: str, timeout: int = 30, headers: Optional[dict[str, str]] = None) -> bool:
        return self.trigger_side_effect("head_fn", url, timeout, headers)

    def post_fn(self, url: str, body: str, timeout: int = 30, headers: Optional[dict[str, str]] = None) -> bool:
        return self.trigger_side_effect("post_fn", url, body, timeout, headers)

    def download_file_fn(
        self,
        url: str,
        download_folder: Optional[str] = None,
        verify_already_downloaded: Optional[bool] = False,
        progress_bar: Optional[bool] = False,
    ) -> bool:
        return self.trigger_side_effect(
            "download_file_fn", url, download_folder, verify_already_downloaded, progress_bar
        )
