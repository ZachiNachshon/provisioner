#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click

from components.runtime.cli.menu_format import GroupedOption, normalize_cli_item
from components.vcs.vcs_opts import CliVersionControlOpts
from provisioner_shared.components.vcs.domain.config import VersionControlConfig

VCS_GROUP_NAME = "Version Control"

VCS_OPT_ORGANIZATION = "organization"
VCS_OPT_REPOSITORY = "repository"
VCS_OPT_BRANCH = "branch"
VCS_OPT_GIT_ACCESS_TOKEN = "git-access-token"


def cli_vcs_opts(vcs_config: Optional[VersionControlConfig] = None) -> Callable:
    from_cfg_git_access_token = None
    if vcs_config is not None and hasattr(vcs_config, "github") and hasattr(vcs_config.github, "git_access_token"):
        from_cfg_git_access_token = vcs_config.github.git_access_token

    # Important !
    # This is the actual click decorator, the signature is critical for click to work
    def decorator_without_params(func: Callable) -> Callable:
        @click.option(
            f"--{VCS_OPT_ORGANIZATION}",
            default=None,
            show_default=False,
            help="GitHub organization",
            envvar="GITHUB_ORGANIZATION",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_REPOSITORY}",
            default=None,
            show_default=False,
            help="GitHub Repository name",
            envvar="GITHUB_REPO_NAME",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_BRANCH}",
            default="master",
            help="GitHub branch name",
            envvar="GITHUB_BRANCH_NAME",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_GIT_ACCESS_TOKEN}",
            default=from_cfg_git_access_token,
            help="GitHub access token for accessing installers private repo",
            envvar="GITHUB_ACCESS_TOKEN",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            github_org = kwargs.get(normalize_cli_item(VCS_OPT_ORGANIZATION), None)
            github_repo_name = kwargs.get(normalize_cli_item(VCS_OPT_REPOSITORY), None)
            github_branch_name = kwargs.get(normalize_cli_item(VCS_OPT_BRANCH), None)
            git_access_token = kwargs.get(normalize_cli_item(VCS_OPT_GIT_ACCESS_TOKEN), None)

            CliVersionControlOpts.create(
                github_organization=github_org,
                repository_name=github_repo_name,
                branch_name=github_branch_name,
                git_access_token=git_access_token,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator_without_params
