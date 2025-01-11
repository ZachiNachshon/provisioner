#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click

from components.runtime.cli.menu_format import GroupedOption, get_nested_value, normalize_cli_item
from components.vcs.vcs_opts import VCS_CLICK_CTX_NAME, CliVersionControlOpts
from provisioner_shared.components.vcs.domain.config import VersionControlConfig

VCS_GROUP_NAME = "Version Control"

VCS_OPT_ORGANIZATION = "organization"
VCS_OPT_REPOSITORY = "repository"
VCS_OPT_BRANCH = "branch"
VCS_OPT_GIT_ACCESS_TOKEN = "git-access-token"


def cli_vcs_opts(vcs_config: Optional[VersionControlConfig] = None) -> Callable:
    from_cfg_organization = get_nested_value(vcs_config, path="github.organization", default=None)
    from_cfg_repository = get_nested_value(vcs_config, path="github.repository", default=None)
    from_cfg_branch = get_nested_value(vcs_config, path="github.branch", default=None)
    from_cfg_git_access_token = get_nested_value(vcs_config, path="github.git_access_token", default=None)

    # Important !
    # This is the actual click decorator, the signature is critical for click to work
    def decorator_without_params(func: Callable) -> Callable:
        @click.option(
            f"--{VCS_OPT_ORGANIZATION}",
            default=from_cfg_organization,
            show_default=True,
            help="GitHub organization",
            envvar="GITHUB_ORGANIZATION",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_REPOSITORY}",
            default=from_cfg_repository,
            show_default=True,
            help="GitHub Repository name",
            envvar="GITHUB_REPO_NAME",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_BRANCH}",
            default=from_cfg_branch,
            show_default=True,
            help="GitHub branch name",
            envvar="GITHUB_BRANCH_NAME",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @click.option(
            f"--{VCS_OPT_GIT_ACCESS_TOKEN}",
            default=from_cfg_git_access_token,
            show_default=False,
            help="GitHub access token for accessing private repositories",
            envvar="GITHUB_ACCESS_TOKEN",
            cls=GroupedOption,
            group=VCS_GROUP_NAME,
        )
        @wraps(func)
        @click.pass_context
        def wrapper(ctx, *args: Any, **kwargs: Any) -> Any:
            github_org = kwargs.pop(normalize_cli_item(VCS_OPT_ORGANIZATION), None)
            github_repo_name = kwargs.pop(normalize_cli_item(VCS_OPT_REPOSITORY), None)
            github_branch_name = kwargs.pop(normalize_cli_item(VCS_OPT_BRANCH), None)
            git_access_token = kwargs.pop(normalize_cli_item(VCS_OPT_GIT_ACCESS_TOKEN), None)

            # Add it to the context object
            if ctx.obj is None:
                ctx.obj = {}

            ctx.obj[VCS_CLICK_CTX_NAME] = CliVersionControlOpts(
                organization=github_org,
                repository=github_repo_name,
                branch=github_branch_name,
                git_access_token=git_access_token,
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator_without_params
