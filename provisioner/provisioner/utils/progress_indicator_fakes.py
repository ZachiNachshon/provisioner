#!/usr/bin/env python3

from typing import Any, Callable, Optional
from unittest.mock import MagicMock

from requests import Response

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.progress_indicator import ProgressIndicator


class FakeProgressIndicator(ProgressIndicator):
    class FakeStatus(TestFakes, ProgressIndicator.Status):
        def __init__(self, dry_run: bool, verbose: bool, non_interactive: bool) -> None:
            TestFakes.__init__(self)
            ProgressIndicator.Status.__init__(self, dry_run=dry_run, verbose=verbose, non_interactive=non_interactive)

        @staticmethod
        def create(ctx: Context) -> "FakeProgressIndicator.FakeStatus":
            fake = FakeProgressIndicator.FakeStatus(
                dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose(), non_interactive=ctx.is_non_interactive()
            )
            fake.long_running_process_fn = MagicMock(side_effect=fake.long_running_process_fn)
            return fake

        def long_running_process_fn(
            self, call: Callable, desc_run: Optional[str] = None, desc_end: Optional[str] = None
        ) -> Any:
            return self.trigger_side_effect("long_running_process_fn", call, desc_run, desc_end)

    class FakeProgressBar(TestFakes, ProgressIndicator.ProgressBar):
        def __init__(self, dry_run: bool, verbose: bool, non_interactive: bool) -> None:
            TestFakes.__init__(self)
            ProgressIndicator.ProgressBar.__init__(
                self, io_utils=None, dry_run=dry_run, verbose=verbose, non_interactive=non_interactive
            )

        @staticmethod
        def create(ctx: Context) -> "FakeProgressIndicator.FakeStatus":
            fake = FakeProgressIndicator.FakeProgressBar(
                dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose(), non_interactive=ctx.is_non_interactive()
            )
            fake.download_file_fn = MagicMock(side_effect=fake.download_file_fn)
            return fake

        def download_file_fn(self, response: Response, download_folder: str) -> Any:
            return self.trigger_side_effect("download_file_fn", response, download_folder)

    _status: FakeStatus = None
    _progress_bar: FakeProgressBar = None

    def get_status(self) -> FakeStatus:
        return self._status

    def get_progress_bar(self) -> FakeProgressBar:
        return self._progress_bar

    def __init__(self, status: ProgressIndicator.Status, progress_bar: ProgressIndicator.ProgressBar) -> None:
        self._status = status
        self._progress_bar = progress_bar

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool, non_interactive: bool) -> "FakeProgressIndicator":
        return FakeProgressIndicator(
            FakeProgressIndicator.FakeStatus(dry_run=dry_run, verbose=verbose, non_interactive=non_interactive),
            FakeProgressIndicator.FakeProgressBar(dry_run=dry_run, verbose=verbose, non_interactive=non_interactive),
        )

    @staticmethod
    def create(ctx: Context) -> "FakeProgressIndicator":
        return FakeProgressIndicator._create_fake(ctx.is_dry_run(), ctx.is_verbose(), ctx.is_non_interactive())
