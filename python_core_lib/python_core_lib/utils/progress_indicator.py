#!/usr/bin/env python3

import concurrent
import functools
import os
import time
from typing import Any, Callable, Optional

from loguru import logger
from requests import Response
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from python_core_lib.colors.color import *
from python_core_lib.infra.context import Context
from python_core_lib.utils.io_utils import IOUtils


class ProgressIndicator:
    class Status:

        _dry_run: bool = None
        _verbose: bool = None

        def __init__(self, dry_run: bool, verbose: bool) -> None:
            self._dry_run = dry_run
            self._verbose = verbose

        def _get_rich_status_indicator(self) -> Console:
            return Console(log_path=False)

        def _inc_based_status_indicator(self, console: Console, future, desc_run: str, desc_end: str) -> Any:
            """
            Display status indicator based on expected time increments.
            Complete early if future completes.
            Wait for future if it doesn't complete in expected_time.
            """
            # with self._get_rich_status_indicator() as console:
            with console:
                with console.status(f"[bold cyan]{desc_run}...", spinner="dots"):
                    try:
                        result = future.result()
                        console.log(f"[green]{desc_end}")
                        return result
                    except Exception as ex:
                        console.print()
                        console.log(f"[red]{desc_end}")
                        console.print()
                        raise ex

        def _long_running_process(
            self, call: Callable, desc_run: Optional[str] = None, desc_end: Optional[str] = None
        ) -> Any:

            if self._dry_run:
                logger.debug("Skipping status indicator on dry-run mode.")
                return call()

            rich_console = self._get_rich_status_indicator()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call)
                return self._inc_based_status_indicator(rich_console, future, desc_run, desc_end)

        long_running_process_fn = _long_running_process

    class ProgressBar:

        _dry_run: bool = None
        _verbose: bool = None
        _io_utils: IOUtils = None

        def __init__(self, io_utils: IOUtils, dry_run: bool, verbose: bool) -> None:
            self._dry_run = dry_run
            self._verbose = verbose
            self._io_utils = io_utils

        def _get_rich_progress_bar(self) -> Progress:
            console = Console(log_path=False)
            return Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                "Elapsed:",
                TimeElapsedColumn(),
                "Remaining:",
                TimeRemainingColumn(),
                console=console,
            )

        def _get_rich_download_progress_bar(self) -> Progress:
            console = Console(log_path=False)
            return Progress(
                TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                BarColumn(bar_width=70),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                console=console,
            )

        def _inc_based_progress_bar(self, future, expected_time: int, increments: int, desc: str) -> Any:
            """
            Display progress bar based on expected time increments.
            Complete early if future completes.
            Wait for future if it doesn't complete in expected_time.
            """
            interval = expected_time / increments
            with self._get_rich_progress_bar() as pbar:
                try:
                    task = pbar.add_task(f"[cyan]{desc}", total=expected_time)
                    for i in range(increments - 1):
                        if future.done():
                            # End progress bar, reach 100%
                            pbar.update(task, description=f"[green]{desc}", completed=expected_time)
                            return future.result()
                        else:
                            time.sleep(interval)
                            pbar.update(task, advance=i)
                    # In case future hasn't completed, wait
                    result = future.result()
                    pbar.update(task, description=f"[green]{desc}", completed=expected_time)
                    return result
                except Exception as ex:
                    # End progress bar, failed
                    pbar.update(task, description=f"[red]{desc}")
                    raise ex

        def _long_running_process(
            self,
            call: Callable,
            expected_time: Optional[int] = 21,
            increments: Optional[int] = 20,
            desc: Optional[str] = None,
        ) -> Any:

            if self._dry_run:
                logger.debug("Skipping progress bar on dry-run mode.")
                return call()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call)
                return self._inc_based_progress_bar(future, expected_time, increments, desc)

        def _inc_based_download_file_progress_bar(self, response: Response, download_folder: str) -> Any:
            def _read_base_url_if_redirect(resp: Response) -> str:
                if resp.history:
                    for resp in resp.history:
                        if resp.status_code == 302:
                            return resp.url
                return resp.url

            """Copy data from a url to a local file."""
            with self._get_rich_download_progress_bar() as pbar:
                url = _read_base_url_if_redirect(response)
                filename = url.split("/")[-1]
                self._io_utils.create_directory_fn(download_folder)
                download_file_path = os.path.join(download_folder, filename)

                task_id = pbar.add_task(description="download", filename=filename, start=False)
                file_size = int(response.headers.get("Content-Length", 0))
                if file_size == 0:
                    logger.warning("Unknown total file size, progress bar might fail")
                response.raw.read = functools.partial(response.raw.read, decode_content=True)

                # This will break if the response doesn't contain content length
                pbar.update(task_id, total=file_size)
                with open(download_file_path, "wb") as dest_file:
                    pbar.start_task(task_id)
                    for data in response.iter_content(chunk_size=32768):
                        dest_file.write(data)
                        pbar.update(task_id, advance=len(data))

                pbar.console.log(f"Downloaded {download_file_path}")

        def _download_file(self, response: Response, download_folder: str) -> Any:
            if self._dry_run:
                logger.debug("Skipping progress bar on dry-run mode.")
                return ""

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._inc_based_download_file_progress_bar, response, download_folder)
                return future.result()

        long_running_process_fn = _long_running_process
        download_file_fn = _download_file

    status: Status = None
    progress_bar: ProgressBar = None

    def __init__(self, status: Status, progress_bar: ProgressBar) -> None:
        self.status = status
        self.progress_bar = progress_bar

    @staticmethod
    def create(
        ctx: Context, io_utils: IOUtils, status: Optional[Status] = None, progress_bar: Optional[ProgressBar] = None
    ) -> "ProgressIndicator":

        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating progress bar (dry_run: {dry_run}, verbose: {verbose})...")
        return ProgressIndicator(
            status if status else ProgressIndicator.Status(dry_run, verbose),
            progress_bar if progress_bar else ProgressIndicator.ProgressBar(io_utils, dry_run, verbose),
        )
