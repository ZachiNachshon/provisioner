#!/usr/bin/env python3

from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.httpclient import HttpClient, HttpResponse
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.printer import Printer


class FakeHttpClient(HttpClient):

    __registered_get_requests: List[str] = None
    __registered_post_requests: List[str] = None
    __registered_downloaded_files: List[str] = None

    __mocked_downloaded_file_response: dict[str, str] = None
    __mocked_get_response: dict[str, HttpResponse] = None
    __mocked_post_response: dict[str, HttpResponse] = None

    def __init__(self, io_utils: IOUtils, printer: Printer, dry_run: bool, verbose: bool):
        super().__init__(io_utils=io_utils, printer=printer, dry_run=dry_run, verbose=verbose)
        self.__registered_get_requests = []
        self.__registered_post_requests = []
        self.__registered_downloaded_files = []

        self.__mocked_downloaded_file_response = {}
        self.__mocked_get_response = {}
        self.__mocked_post_response = {}

    @staticmethod
    def _create_fake(io_utils: IOUtils, printer: Printer, dry_run: bool, verbose: bool) -> "FakeHttpClient":

        http_client = FakeHttpClient(io_utils=io_utils, printer=printer, dry_run=dry_run, verbose=verbose)
        http_client.get_fn = lambda url, timeout=30, headers=None: http_client._url_selector(url)
        http_client.post_fn = lambda url, body, timeout=30, headers=None: http_client._url_selector(url)
        http_client.download_file_fn = lambda url, download_folder=None, verify_already_downloaded=False, progress_bar=False: http_client._register_download_file_response(
            url
        )
        return http_client

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils, printer: Printer = None) -> "FakeHttpClient":
        return FakeHttpClient._create_fake(
            io_utils=io_utils, printer=printer, dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose()
        )

    def mock_download_file_response(self, download_url: str, downloaded_file_path: str):
        self.__mocked_downloaded_file_response[download_url] = downloaded_file_path

    def _register_download_file_response(self, download_url: str):
        self.__registered_downloaded_files.append(download_url)
        if download_url in self.__mocked_downloaded_file_response:
            return self.__mocked_downloaded_file_response[download_url]
        return None

    def assert_download_file(self, download_url: str) -> None:
        if download_url not in self.__registered_downloaded_files:
            raise FakeEnvironmentAssertionError(
                f"HTTP client expected a download file request but it never called. message: {download_url}"
            )

    def mock_get_response(self, download_url: str, expected_response: HttpResponse):
        self.__mocked_get_response[download_url] = expected_response

    def _register_get_request(self, download_url: str):
        self.__registered_get_requests.append(download_url)
        if download_url in self.__mocked_get_response:
            return self.__mocked_get_response[download_url]
        return None

    def assert_get_request(self, download_url: str) -> None:
        if download_url not in self.__registered_get_requests:
            raise FakeEnvironmentAssertionError(
                f"HTTP client expected a GET request but it never called. message: {download_url}"
            )

    def mock_post_response(self, download_url: str, expected_response: HttpResponse):
        self.__mocked_post_response[download_url] = expected_response

    def _register_post_request(self, download_url: str):
        self.__registered_post_requests.append(download_url)
        if download_url in self.__mocked_post_response:
            return self.__mocked_post_response[download_url]
        return None

    def assert_post_request(self, download_url: str) -> None:
        if download_url not in self.__registered_post_requests:
            raise FakeEnvironmentAssertionError(
                f"HTTP client expected a POST request but it never called. message: {download_url}"
            )
