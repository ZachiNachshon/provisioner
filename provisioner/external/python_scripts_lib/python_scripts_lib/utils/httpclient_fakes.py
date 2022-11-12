#!/usr/bin/env python3

from ..infra.context import Context
from .httpclient import HttpClient, HttpResponse
from .io_utils import IOUtils
from .printer import Printer


class FakeHttpClient(HttpClient):

    registered_urls: dict[str, HttpResponse] = None
    registered_download_files: dict[str, str] = None

    def __init__(self, io_utils: IOUtils, printer: Printer, dry_run: bool, verbose: bool):
        super().__init__(io_utils=io_utils, printer=printer, dry_run=dry_run, verbose=verbose)
        self.registered_urls = {}
        self.registered_download_files = {}

    @staticmethod
    def _create_fake(io_utils: IOUtils, printer: Printer, dry_run: bool, verbose: bool) -> "FakeHttpClient":

        http_client = FakeHttpClient(io_utils=io_utils, printer=printer, dry_run=dry_run, verbose=verbose)
        http_client.get_fn = lambda url, timeout=30, headers=None: http_client._url_selector(url)
        http_client.post_fn = lambda url, body, timeout=30, headers=None: http_client._url_selector(url)
        http_client.download_file_fn = lambda url, download_folder=None, verify_already_downloaded=False, progress_bar=False: http_client._download_file_selector(
            url
        )
        return http_client

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils, printer: Printer = None) -> "FakeHttpClient":
        return FakeHttpClient._create_fake(
            io_utils=io_utils, printer=printer, dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose()
        )

    def register_url_response(self, url: str, expected_response: HttpResponse):
        # When opting to use the FakeHttpClient instead of mocking via @mock.patch, we'll override the run function
        self.registered_urls[url] = expected_response

    def _url_selector(self, url: str) -> HttpResponse:
        if url not in self.registered_urls:
            raise LookupError("Fake http client url is not defined. name: " + url)
        return self.registered_urls.get(url)

    def register_download_file_response(self, url: str, expected_file_path: str):
        # When opting to use the FakeHttpClient instead of mocking via @mock.patch, we'll override the run function
        self.registered_download_files[url] = expected_file_path

    def _download_file_selector(self, url: str) -> str:
        if url not in self.registered_download_files:
            raise LookupError("Fake http client download file url is not defined. name: " + url)
        return self.registered_download_files.get(url)
