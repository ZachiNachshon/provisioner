#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click
from loguru import logger

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
            organization = kwargs.pop(normalize_cli_item(VCS_OPT_ORGANIZATION), None)
            repository = kwargs.pop(normalize_cli_item(VCS_OPT_REPOSITORY), None)
            branch = kwargs.pop(normalize_cli_item(VCS_OPT_BRANCH), None)
            git_access_token = kwargs.pop(normalize_cli_item(VCS_OPT_GIT_ACCESS_TOKEN), None)

            # Add it to the context object
            if ctx.obj is None:
                ctx.obj = {}

            if VCS_CLICK_CTX_NAME not in ctx.obj:
                # First-time initialization
                ctx.obj[VCS_CLICK_CTX_NAME] = CliVersionControlOpts(
                    organization=organization,
                    repository=repository,
                    branch=branch,
                    git_access_token=git_access_token,
                )
                logger.debug("Initialized CliVersionControlOpts for the first time.")
            else:
                # Update only the relevant fields if they change
                cvs_opts = ctx.obj[VCS_CLICK_CTX_NAME]

                if organization and not cvs_opts.organization:
                    cvs_opts.organization = True

                if repository and not cvs_opts.repository:
                    cvs_opts.repository = True

                if branch and not cvs_opts.branch:
                    cvs_opts.branch = True

                if git_access_token and not cvs_opts.git_access_token:
                    cvs_opts.git_access_token = True

            return func(*args, **kwargs)

        return wrapper

    return decorator_without_params
