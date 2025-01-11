#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click
from components.remote.domain.config import RemoteConfig
from components.vcs.vcs_opts import CliVersionControlOpts

from provisioner_shared.components.vcs.domain.config import \
    VersionControlConfig


def cli_vcs_opts(vcs_config: Optional[VersionControlConfig] = None) -> Callable:
    from_cfg_git_access_token = None
    if (
        vcs_config is not None
        and hasattr(vcs_config, "github")
        and hasattr(vcs_config.github, "git_access_token")
    ):
        from_cfg_git_access_token = vcs_config.github.git_access_token

    # Important ! 
    # This is the actual click decorator, the signature is critical for click to work
    def decorator_without_params(func: Callable) -> Callable:
        @click.option(
            "--github-org",
            default=None,
            show_default=False,
            help="GitHub organization",
            envvar="GITHUB_ORGANIZATION",
        )
        @click.option(
            "--github-repo-name",
            default=None,
            show_default=False,
            help="Repository name",
            envvar="GITHUB_REPO_NAME",
        )
        @click.option(
            "--github-branch-name",
            default="master",
            help="Repository branch name",
            envvar="GITHUB_BRANCH_NAME",
        )
        @click.option(
            "--git-access-token",
            default=from_cfg_git_access_token,
            help="GitHub access token for accessing installers private repo",
            envvar="GITHUB_ACCESS_TOKEN",
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            github_org = kwargs.get("github_org", None)
            github_repo_name = kwargs.get("github_repo_name", None)
            github_branch_name = kwargs.get("github_branch_name", None)
            git_access_token = kwargs.get("git_access_token", None)

            CliVersionControlOpts.create(
                github_organization=github_org,
                repository_name=github_repo_name,
                branch_name=github_branch_name,
                git_access_token=git_access_token,
            )
            return func(*args, **kwargs)
        
        return wrapper
        
    return decorator_without_params
      