#!/usr/bin/env python3

from ..infra.context import Context
from .io_utils import IOUtils
from .progress_indicator import ProgressIndicator


class FakeProgressIndicator(ProgressIndicator):
    class FakeStatus(ProgressIndicator.Status):
        def __init__(self, dry_run: bool, verbose: bool) -> None:
            super().__init__(dry_run=dry_run, verbose=verbose)

        @staticmethod
        def _create_fake(dry_run: bool, verbose: bool) -> "FakeProgressIndicator":
            fake_status = FakeProgressIndicator.FakeStatus(dry_run=dry_run, verbose=verbose)
            fake_status.long_running_process_fn = lambda call, desc_run=None, desc_end=None: call()
            return fake_status

    class FakeProgressBar(ProgressIndicator.ProgressBar):
        def __init__(self, io_utils: IOUtils, dry_run: bool, verbose: bool) -> None:
            super().__init__(io_utils=io_utils, dry_run=dry_run, verbose=verbose)

        @staticmethod
        def _create_fake(dry_run: bool, verbose: bool) -> "FakeProgressIndicator":
            fake_pbar = FakeProgressIndicator.FakeProgressBar(io_utils=None, dry_run=dry_run, verbose=verbose)
            fake_pbar.long_running_process_fn = lambda call, expected_time=None, increments=None, desc=None: call()
            return fake_pbar

    status: ProgressIndicator.Status = None
    progress_bar: ProgressIndicator.ProgressBar = None

    def __init__(self, status: ProgressIndicator.Status, progress_bar: ProgressIndicator.ProgressBar) -> None:

        self.status = status
        self.progress_bar = progress_bar

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool) -> "FakeProgressIndicator":
        return FakeProgressIndicator(
            FakeProgressIndicator.FakeStatus(dry_run, verbose),
            FakeProgressIndicator.FakeProgressBar(io_utils=None, dry_run=dry_run, verbose=verbose),
        )

    @staticmethod
    def create(ctx: Context) -> "FakeProgressIndicator":
        return FakeProgressIndicator._create_fake(ctx.is_dry_run(), ctx.is_verbose())
