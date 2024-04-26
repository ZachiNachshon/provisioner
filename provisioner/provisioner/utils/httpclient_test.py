#!/usr/bin/env python3

import unittest
from unittest import mock

import requests

from provisioner.errors.cli_errors import DownloadFileException
from provisioner.test_lib.assertions import Assertion
from provisioner.test_lib.test_env import TestEnv
from provisioner.utils.httpclient import HttpClient, HttpResponse


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner/utils/httpclient_test.py
#
class HttpClientTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_http_client(self) -> HttpClient:
        return HttpClient.create(
            self.env.get_context(),
            io_utils=self.env.get_collaborators().io_utils(),
            progress_indicator=self.env.get_collaborators().progress_indicator(),
            printer=self.env.get_collaborators().printer(),
        )

    def test_get_raw_client(self):
        http_client = self.create_fake_http_client()
        raw_client = http_client.raw_client()
        self.assertIsNotNone(raw_client)

    @mock.patch("requests.request")
    def test_request_successfully(self, get_call: mock.MagicMock):
        lib_resp = requests.Response()
        lib_resp._content = str.encode("response text")
        lib_resp.status_code = 200
        get_call.side_effect = [lib_resp]

        http_client = self.create_fake_http_client()
        response = http_client._base_request(
            method="TEST", url="http://some-url", body="test json", timeout=60, headers={"key": "value"}
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "response text")

        get_call_kwargs = get_call.call_args.kwargs
        self.assertEqual("TEST", get_call_kwargs["method"])
        self.assertEqual("http://some-url", get_call_kwargs["url"])
        self.assertEqual("test json", get_call_kwargs["data"])
        self.assertEqual(60, get_call_kwargs["timeout"])
        self.assertEqual({"key": "value"}, get_call_kwargs["headers"])

    @mock.patch("requests.request")
    def test_get_fail_without_exception(self, get_call: mock.MagicMock):
        lib_resp = requests.Response()
        lib_resp._content = str.encode("response text")
        lib_resp.status_code = 404
        get_call.side_effect = [lib_resp]

        http_client = self.create_fake_http_client()
        response = http_client._base_request(method="TEST", url="http://some-url")
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.error)
        self.assertIn("HTTP TEST request failed", response.error.message)
        self.assertIn("404", response.error.message)

    @mock.patch("requests.request", side_effect=requests.ConnectionError("test connection error"))
    def test_get_fail_on_conn_error(self, get_call: mock.MagicMock):
        http_client = self.create_fake_http_client()
        response = http_client._base_request(method="TEST", url="http://some-url")
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.error)
        self.assertIn("test connection error", response.error.message)

    @mock.patch("requests.request", side_effect=requests.Timeout("test timeout"))
    def test_get_fail_on_timeout(self, get_call: mock.MagicMock):
        http_client = self.create_fake_http_client()
        response = http_client._base_request(method="TEST", url="http://some-url")
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.error)
        self.assertIn("test timeout", response.error.message)
        self.assertTrue(response.error.is_timeout)

    @mock.patch(
        "provisioner.utils.httpclient.HttpClient._base_request",
        side_effect=[HttpResponse(raw=None, content="test content")],
    )
    def test_get_arguments(self, base_req_call: mock.MagicMock):
        http_client = self.create_fake_http_client()
        response = http_client.get_fn(url="http://some-url", timeout=60, headers={"key": "value"})
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "test content")

        get_call_kwargs = base_req_call.call_args.kwargs
        self.assertEqual("http://some-url", get_call_kwargs["url"])
        self.assertEqual(60, get_call_kwargs["timeout"])
        self.assertEqual({"key": "value"}, get_call_kwargs["headers"])

    @mock.patch(
        "provisioner.utils.httpclient.HttpClient._base_request",
        side_effect=[HttpResponse(raw=None, content="test content")],
    )
    def test_post_arguments(self, base_req_call: mock.MagicMock):
        http_client = self.create_fake_http_client()
        response = http_client.post_fn(url="http://some-url", body="test json", timeout=60, headers={"key": "value"})
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "test content")

        get_call_kwargs = base_req_call.call_args.kwargs
        self.assertEqual("http://some-url", get_call_kwargs["url"])
        self.assertEqual("test json", get_call_kwargs["body"])
        self.assertEqual(60, get_call_kwargs["timeout"])
        self.assertEqual({"key": "value"}, get_call_kwargs["headers"])

    @mock.patch("requests.get")
    def test_download_file_success_with_progress_bar(self, get_call: mock.MagicMock):
        lib_resp = requests.Response()
        lib_resp._content = str.encode("downloaded file")
        lib_resp.status_code = 200
        get_call.side_effect = [lib_resp]

        test_env = TestEnv.create()
        fake_io = test_env.get_collaborators().io_utils()
        fake_io.on("create_directory_fn", str).side_effect = None
        fake_io.on("file_exists_fn", str).return_value = False

        p_indicator = test_env.get_collaborators().progress_indicator()
        fake_p_bar = p_indicator.get_progress_bar()
        fake_p_bar.on("download_file_fn", requests.Response, str).side_effect = None

        http_client = HttpClient.create(
            self.env.get_context(),
            io_utils=fake_io,
            progress_indicator=p_indicator,
            printer=None,
        )

        filepath = http_client.download_file_fn(
            url="http://some-url/filename.tar.gz",
            download_folder="/test/download/folder",
            verify_already_downloaded=True,
            progress_bar=True,
        )

        self.assertIsNotNone(filepath)
        self.assertEqual(filepath, "/test/download/folder/filename.tar.gz")

    @mock.patch("shutil.copyfileobj")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("requests.get")
    def test_download_file_success_no_progres_bar(
        self, get_call: mock.MagicMock, mock_open: mock.MagicMock, mock_copy: mock.MagicMock
    ):
        lib_resp = requests.Response()
        lib_resp._content = str.encode("downloaded file")
        lib_resp.status_code = 200
        get_call.side_effect = [lib_resp]

        test_env = TestEnv.create()
        fake_io = test_env.get_collaborators().io_utils()
        fake_io.on("create_directory_fn", str).side_effect = None
        fake_io.on("file_exists_fn", str).return_value = False

        fake_printer = test_env.get_collaborators().printer()
        fake_printer.on("print_fn", str).side_effect = lambda msg: self.assertIn("Downloading file", msg)

        http_client = HttpClient.create(
            self.env.get_context(),
            io_utils=fake_io,
            progress_indicator=None,
            printer=fake_printer,
        )

        filepath = http_client.download_file_fn(
            url="http://some-url/filename.tar.gz",
            download_folder="/test/download/folder",
            verify_already_downloaded=True,
            progress_bar=False,
        )

        self.assertIsNotNone(filepath)
        self.assertEqual(filepath, "/test/download/folder/filename.tar.gz")
        # Assert that the file was opened in write binary mode
        mock_open.assert_called_once_with("/test/download/folder/filename.tar.gz", "wb")
        # Assert that copyfileobj was called
        mock_copy.assert_called_once()

    def test_download_file_already_exists(self):
        test_env = TestEnv.create()
        fake_io = test_env.get_collaborators().io_utils()
        fake_io.on("create_directory_fn", str).side_effect = None
        fake_io.on("file_exists_fn", str).return_value = True

        p_indicator = test_env.get_collaborators().progress_indicator()
        fake_p_bar = p_indicator.get_progress_bar()
        fake_p_bar.on("download_file_fn", requests.Response, str).side_effect = None

        http_client = HttpClient.create(
            self.env.get_context(),
            io_utils=fake_io,
            progress_indicator=p_indicator,
            printer=None,
        )

        filepath = http_client.download_file_fn(
            url="http://some-url/filename.tar.gz",
            download_folder="/test/download/folder",
            verify_already_downloaded=True,
            progress_bar=True,
        )

        self.assertIsNotNone(filepath)
        self.assertEqual(filepath, "/test/download/folder/filename.tar.gz")

    @mock.patch("requests.get")
    def test_download_file_exception(self, get_call: mock.MagicMock):
        lib_resp = requests.Response()
        lib_resp.status_code = 400
        get_call.side_effect = [lib_resp]

        test_env = TestEnv.create()
        fake_io = test_env.get_collaborators().io_utils()
        fake_io.on("create_directory_fn", str).side_effect = None
        fake_io.on("file_exists_fn", str).return_value = False

        http_client = HttpClient.create(
            self.env.get_context(),
            io_utils=fake_io,
            progress_indicator=None,
            printer=None,
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=DownloadFileException,
            method_to_run=lambda: http_client.download_file_fn(
                url="http://some-url/filename.tar.gz",
                download_folder="/test/download/folder",
                verify_already_downloaded=True,
                progress_bar=True,
            ),
        )
