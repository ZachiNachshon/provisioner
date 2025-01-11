#!/usr/bin/env python3

from typing import Optional

import click
from loguru import logger

VCS_CLICK_CTX_NAME = "cli_vcs_opts"

class CliVersionControlOpts:

    def __init__(
        self,
        github_organization: Optional[str] = None,
        repository_name: Optional[str] = None,
        branch_name: Optional[str] = None,
        git_access_token: Optional[str] = None,
    ) -> None:

        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.git_access_token = git_access_token

    @staticmethod
    def from_click_ctx(ctx: click.Context) -> Optional["CliVersionControlOpts"]:
        """Returns the current singleton instance, if any."""
        return ctx.obj.get(VCS_CLICK_CTX_NAME, None) if ctx.obj else None

    def print(self) -> None:
        logger.debug(
            "CliVersionControlOpts: \n"
            + f"  github_organization: {self.github_organization}\n"
            + f"  repository_name: {self.repository_name}\n"
            + f"  branch_name: {self.branch_name}\n"
            + "  git_access_token: REDACTED\n"
        )
