#!/usr/bin/env python3

from typing import Optional

import click
from loguru import logger

VCS_CLICK_CTX_NAME = "cli_vcs_opts"

class CliVersionControlOpts:

    def __init__(
        self,
        organization: Optional[str] = None,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        git_access_token: Optional[str] = None,
    ) -> None:

        self.organization = organization
        self.repository = repository
        self.branch = branch
        self.git_access_token = git_access_token

    @staticmethod
    def from_click_ctx(ctx: click.Context) -> Optional["CliVersionControlOpts"]:
        """Returns the current singleton instance, if any."""
        return ctx.obj.get(VCS_CLICK_CTX_NAME, None) if ctx.obj else None

    def print(self) -> None:
        logger.debug(
            "CliVersionControlOpts: \n"
            + f"  organization: {self.organization}\n"
            + f"  repository: {self.repository}\n"
            + f"  branch: {self.branch}\n"
            + "  git_access_token: REDACTED\n"
        )
