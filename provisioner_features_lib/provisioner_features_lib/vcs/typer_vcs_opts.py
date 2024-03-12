#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger

from provisioner_features_lib.vcs.domain.config import VersionControlConfig

VERSION_CONTROL_HELP_TITLE = "Version Control"


class TyperVersionControl:

    _vcs_config: VersionControlConfig = None
    _cli_vcs_opts: "CliVersionControlOpts" = None

    def __init__(self, vcs_config: VersionControlConfig = None) -> None:
        self._vcs_config = vcs_config

    def github_org(self):
        return typer.Option(
            None,
            show_default=False,
            help="GitHub organization",
            envvar="GITHUB_ORGANIZATION",
            rich_help_panel=VERSION_CONTROL_HELP_TITLE,
        )

    def github_repo_name(self):
        return typer.Option(
            None,
            show_default=False,
            help="Repository name",
            envvar="GITHUB_REPO_NAME",
            rich_help_panel=VERSION_CONTROL_HELP_TITLE,
        )

    def github_branch_name(self):
        return typer.Option(
            "master",
            help="Repository branch name",
            envvar="GITHUB_BRANCH_NAME",
            rich_help_panel=VERSION_CONTROL_HELP_TITLE,
        )

    def git_access_token(self, from_config: str = None):
        return typer.Option(
            default=from_config,
            show_default=False,
            help="GitHub access token for accessing installers private repo",
            envvar="GITHUB_ACCESS_TOKEN",
            rich_help_panel=VERSION_CONTROL_HELP_TITLE,
        )

    def as_typer_callback(self):
        from_cfg_git_access_token = None
        if self._vcs_config is not None and self._vcs_config.github is not None:
            from_cfg_git_access_token = self._vcs_config.github.git_access_token
            print(f"setting {from_cfg_git_access_token}")

        def typer_callback(
            org: str = self.github_org(),
            repo: str = self.github_repo_name(),
            branch: str = self.github_branch_name(),
            git_access_token: str = self.git_access_token(from_cfg_git_access_token),
        ):

            self._cli_vcs_opts = CliVersionControlOpts(
                org,
                repo,
                branch,
                git_access_token,
            )

        return typer_callback

    def to_cli_opts(self) -> "CliVersionControlOpts":
        return self._cli_vcs_opts


class CliVersionControlOpts:

    github_organization: Optional[str]
    repository_name: Optional[str]
    branch_name: Optional[str]
    git_access_token: Optional[str]

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

    def print(self) -> None:
        logger.debug(
            "CliVersionControlOpts: \n"
            + f"  github_organization: {self.github_organization}\n"
            + f"  repository_name: {self.repository_name}\n"
            + f"  branch_name: {self.branch_name}\n"
            + f"  git_access_token: {self.git_access_token}\n"
        )
