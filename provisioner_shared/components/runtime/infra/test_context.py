#!/usr/bin/env python3

from typing import Dict, Optional

from loguru import logger

from provisioner_shared.components.runtime.cli.modifiers import CliModifiers, PackageManager
from provisioner_shared.components.runtime.utils.os import OsArch
from provisioner_shared.components.runtime.infra.context import Context

class TestingContext(Context):
    def __init__(self, **kwargs):
        super().__init__()
        self.extra_data: Dict[str, any] = kwargs  # Dynamic dictionary for additional attributes

    # Used for 'with' statements
    # with TestingContext.from_context(self.ctx) as test_ctx:
    #   test_ctx.set_extra("key", "value")
    # 
    # def __enter__(self):
    #     """Enables use in 'with' statements."""
    #     return self

    # def __exit__(self, exc_type, exc_value, traceback):
    #     """Handles cleanup if necessary."""
    #     pass  # No specific cleanup needed
    
    @staticmethod
    def from_context(ctx: Context) -> Optional["TestingContext"]:
        """Returns a TestingContext if the given Context is actually an instance of TestingContext; otherwise, returns None."""
        return ctx if isinstance(ctx, TestingContext) else None
        
    @staticmethod
    def create(
        dry_run: Optional[bool] = False,
        verbose: Optional[bool] = False,
        auto_prompt: Optional[bool] = False,
        non_interactive: Optional[bool] = False,
        os_arch: Optional[OsArch] = None,
        pkg_mgr: Optional[PackageManager] = PackageManager.PIP,
        **kwargs
    ) -> "TestingContext":
        """Creates a TestingContext with all Context members and extra dynamic attributes."""
        try:
            ctx = TestingContext(**kwargs)
            ctx.os_arch = os_arch if os_arch else OsArch()
            ctx._dry_run = dry_run
            ctx._verbose = verbose
            ctx._auto_prompt = auto_prompt
            ctx._non_interactive = non_interactive
            ctx._pkg_mgr = pkg_mgr
            return ctx
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create TestingContext object. ex: {}, message: {}", e_name, str(e))

    def set_extra(self, key: str, value: any):
        """Set a key-value pair in the dynamic dictionary."""
        self.extra_data[key] = value

    def get_extra(self, key: str, default: any = None):
        """Retrieve a value from the dynamic dictionary."""
        return self.extra_data.get(key, default)

    def has_extra(self, key: str) -> bool:
        """Check if a key exists in the dynamic dictionary."""
        return key in self.extra_data