#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger

from provisioner_features_lib.anchor.domain.config import AnchorConfig

ANCHOR_HELP_TITLE = "Anchor Opts"


class TyperAnchorOpts:
    """
    Load method MUST be called to populate the config object after values were
    read from local configuration file
    """

    # Static variable
    anchor_config: AnchorConfig = None

    def __init__(self, anchor_config: AnchorConfig = None) -> None:
        self.anchor_config = anchor_config

    @staticmethod
    def load(anchor_config: AnchorConfig) -> None:
        TyperAnchorOpts.anchor_config = anchor_config

    def git_access_token():
        return typer.Option(
            TyperAnchorOpts.anchor_config.github.git_access_token,
            show_default=False,
            help="GitHub access token for accessing installers private repo",
            envvar="GITHUB_ACCESS_TOKEN",
            rich_help_panel=ANCHOR_HELP_TITLE,
        )


class TyperResolvedAnchorOpts:

    _github_access_token: Optional[str] = None

    def __init__(self, git_access_token: Optional[str] = None) -> None:
        self._github_access_token = git_access_token

    @staticmethod
    def create(
        git_access_token: Optional[str] = None,
    ) -> None:

        global GLOBAL_TYPER_CLI_ANCHOR_OPTS
        GLOBAL_TYPER_CLI_ANCHOR_OPTS = TyperResolvedAnchorOpts(git_access_token=git_access_token)


GLOBAL_TYPER_CLI_ANCHOR_OPTS: TyperResolvedAnchorOpts = None


class CliAnchorOpts:
    git_access_token: Optional[str]

    def __init__(self, git_access_token: Optional[str] = None) -> None:
        self.git_access_token = git_access_token

    @staticmethod
    def maybe_get() -> "CliAnchorOpts":
        if GLOBAL_TYPER_CLI_ANCHOR_OPTS:
            return CliAnchorOpts(git_access_token=GLOBAL_TYPER_CLI_ANCHOR_OPTS._github_access_token)
        return None

    def print(self) -> None:
        logger.debug("CliAnchorOpts: \n" + f"  git_access_token: {self.git_access_token}\n")
