#!/usr/bin/env python3

from provisioner_features_lib.anchor.typer_anchor_opts import (
    TyperAnchorOpts,
    TyperResolvedAnchorOpts,
)


def anchor_args_callback(git_access_token: str = TyperAnchorOpts.git_access_token()):
    TyperResolvedAnchorOpts.create(
        git_access_token,
    )
