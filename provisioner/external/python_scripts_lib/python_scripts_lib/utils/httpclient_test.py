#!/usr/bin/env python3

import unittest
from unittest import mock

import requests

from ..infra.context import Context
from ..utils.httpclient import HttpClient, HttpResponse
from ..utils.io_utils_fakes import FakeIOUtils
from ..utils.printer_fakes import FakePrinter


class HttpClientTestShould(unittest.TestCase):
    def create_fake_http_client(self) -> HttpClient:
        ctx = Context.create()
        fake_printer = FakePrinter.create(ctx)
        return HttpClient.create(ctx, io_utils=FakeIOUtils.create(ctx), printer=fake_printer)

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
        "python_scripts_lib.utils.httpclient.HttpClient._base_request",
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
        "python_scripts_lib.utils.httpclient.HttpClient._base_request",
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
