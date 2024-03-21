#!/usr/bin/env python3

from typing import Any, Callable, Optional
from unittest.mock import MagicMock
from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.io_utils import IOUtils
from provisioner.utils.progress_indicator import ProgressIndicator


class FakeProgressIndicator(ProgressIndicator):
    class FakeStatus(TestFakes, ProgressIndicator.Status):
    
        def __init__(self, dry_run: bool, verbose: bool) -> None:
            TestFakes.__init__(self)
            ProgressIndicator.Status.__init__(self, dry_run=dry_run, verbose=verbose)

        @staticmethod
        def create(ctx: Context) -> "FakeProgressIndicator.FakeStatus":
            fake = FakeProgressIndicator.FakeStatus(dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose())
            fake.long_running_process_fn = MagicMock(side_effect=fake.long_running_process_fn)
            return fake

        def long_running_process_fn(
            self, call: Callable, desc_run: Optional[str] = None, desc_end: Optional[str] = None
        ) -> Any:
            return self.trigger_side_effect("long_running_process_fn", call, desc_run, desc_end)
        
    class FakeProgressBar(ProgressIndicator.ProgressBar):
        def __init__(self, io_utils: IOUtils, dry_run: bool, verbose: bool) -> None:
            super().__init__(io_utils=io_utils, dry_run=dry_run, verbose=verbose)

        @staticmethod
        def _create_fake(dry_run: bool, verbose: bool) -> "FakeProgressIndicator":
            fake_pbar = FakeProgressIndicator.FakeProgressBar(io_utils=None, dry_run=dry_run, verbose=verbose)
            fake_pbar.long_running_process_fn = lambda call, expected_time=None, increments=None, desc=None: call()
            return fake_pbar

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
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeProgressIndicator":
        return FakeProgressIndicator(
            FakeProgressIndicator.FakeStatus(dry_run=dry_run, verbose=verbose),
            FakeProgressIndicator.FakeProgressBar(io_utils=None, dry_run=dry_run, verbose=verbose),
        )

    @staticmethod
    def create(ctx: Context) -> "FakeProgressIndicator":
        return FakeProgressIndicator._create_fake(ctx.is_dry_run(), ctx.is_verbose())
