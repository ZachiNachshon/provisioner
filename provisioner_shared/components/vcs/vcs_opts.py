#!/usr/bin/env python3

from typing import Optional

from loguru import logger

class CliVersionControlOpts:

    options: "CliVersionControlOpts" = None

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
    def create(
        github_organization: Optional[str] = None,
        repository_name: Optional[str] = None,
        branch_name: Optional[str] = None,
        git_access_token: Optional[str] = None,
    ) -> None:
        try:
            CliVersionControlOpts.options = CliVersionControlOpts(
                github_organization=github_organization,
                repository_name=repository_name,
                branch_name=branch_name,
                git_access_token=git_access_token,
            )
        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI vcs opts object. ex: {}, message: {}", e_name, str(e))

    def print(self) -> None:
        logger.debug(
            "CliVersionControlOpts: \n"
            + f"  github_organization: {self.github_organization}\n"
            + f"  repository_name: {self.repository_name}\n"
            + f"  branch_name: {self.branch_name}\n"
            + f"  git_access_token: REDACTED\n"
        )
