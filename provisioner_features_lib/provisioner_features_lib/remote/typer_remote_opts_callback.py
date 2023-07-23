#!/usr/bin/env python3

from typing import Optional

from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.typer_remote_opts import (
    TyperRemoteOpts,
    TyperResolvedRemoteOpts,
)


def remote_args_callback(
    environment: RunEnvironment = TyperRemoteOpts.environment(),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
    dry_run: Optional[bool] = TyperRemoteOpts.dry_run(),
    verbose: Optional[bool] = TyperRemoteOpts.verbose(),
    silent: Optional[bool] = TyperRemoteOpts.silent(),
):

    TyperResolvedRemoteOpts.create(
        environment,
        node_username,
        node_password,
        ssh_private_key_file_path,
        ip_discovery_range,
        ConfigResolver.config.remote.hosts,
        dry_run,
        verbose,
        silent,
    )
