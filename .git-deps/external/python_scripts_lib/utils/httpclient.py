#!/usr/bin/env python3

import tempfile
import requests
import shutil
from tqdm.auto import tqdm
import functools
from requests import RequestException
from typing import Optional
from .io_utils import IOUtils
from loguru import logger
from ..errors.cli_errors import DownloadFileException
from ..infra.context import Context


class ErrorResponse:
    message: str = ""
    is_timeout: bool = False

    def __init__(self, request_exception: Optional[RequestException] = None, exception: Optional[Exception] = None):

        if request_exception:
            self.message = str(request_exception)
            self.is_timeout = isinstance(request_exception, requests.Timeout)

        if exception and not request_exception:
            self.message = str(exception)


class HttpResponse:
    raw_res: requests.Response
    error: Optional[ErrorResponse] = None

    def __init__(
        self,
        raw: requests.Response,
        content: str = "",
        request_exception: Optional[RequestException] = None,
        exception: Optional[Exception] = None,
    ):
        self.raw_res = raw
        self.content = content
        if request_exception:
            self.error = ErrorResponse(request_exception=request_exception)

        if exception and not request_exception:
            self.error = ErrorResponse(exception=exception)

    def raw_res(self):
        return self.raw_res

    def success(self) -> bool:
        return self.error is None


class HttpClient:

    _dry_run: bool = None
    _verbose: bool = None
    io: IOUtils = None

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils) -> "HttpClient":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating http client (dry_run: {dry_run}, verbose: {verbose})...")
        client = HttpClient(io_utils, dry_run, verbose)
        return client

    def __init__(self, io_utils: IOUtils, dry_run: bool, verbose: bool) -> None:
        self._dry_run = dry_run
        self._verbose = verbose
        self.io = io_utils

    def raw_client(self):
        return requests

    def _base_request(
        self,
        method: str,
        url: str,
        body: Optional[str] = None,
        timeout: Optional[int] = 30,
        headers: Optional[dict[str, str]] = None,
        stream: Optional[bool] = False,
    ) -> HttpResponse:

        if self._dry_run:
            return HttpResponse(raw_res=None, content="DRY_RUN_HTTP_RESPONSE")

        response = None
        try:
            res = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=timeout,
                stream=stream,
            )
            res.encoding = "utf-8"

            if res.status_code >= 200 and res.status_code <= 299:
                response = HttpResponse(raw=res, content=res.text)
            else:
                err_msg = "HTTP {} request failed. status = {}, message: {}, url: {}, timeout: {}\nbody: {}".format(
                    method, res.status_code, res.text, url, timeout, body
                )
                logger.error(err_msg)
                response = HttpResponse(raw=res, exception=Exception(err_msg))

        except requests.ConnectionError as conn_err:
            logger.error(f"HTTP {method} request failed. ConnectionError = {conn_err}")
            response = HttpResponse(request_exception=conn_err)
        except requests.Timeout as timeout_err:
            logger.error(f"HTTP {method} request failed due to timeout ({timeout} sec)")
            response = HttpResponse(request_exception=timeout_err)

        return response

    def _get(self, url: str, timeout: int = 30, headers: Optional[dict[str, str]] = None) -> HttpResponse:
        return self._base_request("GET", url=url, timeout=timeout, headers=headers)

    def _post(self, url: str, body: str, timeout: int = 30, headers: Optional[dict[str, str]] = None) -> HttpResponse:
        return self._base_request("POST", url=url, body=body, timeout=timeout, headers=headers)

    def _download_file(
        self,
        url: str,
        download_folder: Optional[str] = None,
        verify_already_downloaded: Optional[bool] = False,
        progress_bar: Optional[bool] = False,
    ) -> str:

        if self._dry_run:
            return "DRY_RUN_DOWNLOAD_FILE_PATH"

        download_folder = download_folder if download_folder else tempfile.mkdtemp(prefix="http-client-")
        filename = url.rsplit("/")[-1]
        file_path = "{}/{}".format(download_folder, filename)

        if verify_already_downloaded and self.io.file_exists_fn(file_path):
            logger.debug("Found previously downloaded file. path: {}", file_path)
            return file_path

        r = requests.get(url, stream=True, allow_redirects=True)
        if r.status_code != 200:
            r.raise_for_status()
            raise DownloadFileException(f"Request to {url} returned status code {r.status_code}")

        if progress_bar:
            file_size = int(r.headers.get("Content-Length", 0))
            desc = "(Unknown total file size)" if file_size == 0 else ""
            r.raw.read = functools.partial(r.raw.read, decode_content=True)
            with tqdm.wrapattr(r.raw, "read", total=file_size, desc=desc) as r_raw:
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(r_raw, f)
        else:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        return file_path

    get_fn = _get
    post_fn = _post
    download_file_fn = _download_file
