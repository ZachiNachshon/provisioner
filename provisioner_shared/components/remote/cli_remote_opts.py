#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click
from loguru import logger

from provisioner_shared.components.remote.domain.config import RemoteConfig, RemoteConnectMode, RunEnvironment
from provisioner_shared.components.remote.remote_opts import (
    REMOTE_CLICK_CTX_NAME,
    RemoteOpts,
    RemoteOptsFromConfig,
    RemoteOptsFromConnFlags,
    RemoteOptsFromScanFlags,
    RemoteVerbosity,
)
from provisioner_shared.components.runtime.cli.click_callbacks import mutually_exclusive_callback
from provisioner_shared.components.runtime.cli.menu_format import GroupedOption, get_nested_value, normalize_cli_item
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext

REMOTE_GENERAL_OPTS_GROUP_NAME = "General"
REMOTE_CON_FLAGS_GROUP_NAME = "Flags"
REMOTE_SCAN_LAN_OPTS_GROUP_NAME = "ScanLAN"
REMOTE_EXECUTION_OPTS_GROUP_NAME = "Execution"

REMOTE_OPT_CONNECT_MODE = "connect-mode"
REMOTE_OPT_ENV = "environment"
REMOTE_OPT_NODE_USERNAME = "node-username"
REMOTE_OPT_NODE_PASSWORD = "node-password"
REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH = "ssh-private-key-file-path"
REMOTE_OPT_IP_ADDRESS = "ip-address"
REMOTE_OPT_PORT = "port"
REMOTE_OPT_HOSTNAME = "hostname"
REMOTE_OPT_IP_DISCOVERY_RANGE = "ip-discovery-range"
REMOTE_OPT_VERBOSITY = "verbosity"
REMOTE_OPT_REMOTE_DRY_RUN = "remote-dry-run"


# Define modifiers globally
def cli_remote_opts(remote_config: Optional[RemoteConfig] = None) -> Callable:
    from_cfg_ip_discovery_range = get_nested_value(remote_config, path="lan_scan.ip_discovery_range", default=None)

    # Important !
    # This is the actual click decorator, the signature is critical for click to work
    def decorator_without_params(func: Callable) -> Callable:
        @click.option(
            f"--{REMOTE_OPT_ENV}",
            default="Local",
            show_default=True,
            type=click.Choice([v.value for v in RunEnvironment], case_sensitive=False),
            help="Specify an environment",
            envvar="PROV_ENVIRONMENT",
            cls=GroupedOption,
            group=REMOTE_GENERAL_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_CONNECT_MODE}",
            default="Interactive",
            show_default=True,
            type=click.Choice([v.value for v in RemoteConnectMode], case_sensitive=False),
            help="Specifies the mode to connect to the remote machine",
            envvar="PROV_REMOTE_CONNECT_MODE",
            cls=GroupedOption,
            group=REMOTE_GENERAL_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_NODE_USERNAME}",
            show_default=False,
            help="Remote node username",
            envvar="PROV_NODE_USERNAME",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_NODE_PASSWORD}",
            show_default=False,
            help="Remote node password",
            envvar="PROV_NODE_PASSWORD",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
            callback=mutually_exclusive_callback,
        )
        @click.option(
            f"--{REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH}",
            show_default=False,
            help="Private SSH key local file path",
            envvar="PROV_SSH_PRIVATE_KEY_FILE_PATH",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
            callback=mutually_exclusive_callback,
        )
        @click.option(
            f"--{REMOTE_OPT_IP_ADDRESS}",
            default="",
            help="Remote node IP address",
            envvar="PROV_IP_ADDRESS",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_PORT}",
            default=22,
            show_default=True,
            help="Remote node port",
            envvar="PROV_PORT",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_HOSTNAME}",
            default="",
            help="Remote node host name",
            envvar="PROV_HOSTNAME",
            cls=GroupedOption,
            group=REMOTE_CON_FLAGS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_IP_DISCOVERY_RANGE}",
            default=from_cfg_ip_discovery_range,
            show_default=True,
            help="LAN network IP discovery scan range",
            envvar="PROV_IP_DISCOVERY_RANGE",
            cls=GroupedOption,
            group=REMOTE_SCAN_LAN_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_VERBOSITY}",
            default=RemoteVerbosity.Normal.value,
            show_default=True,
            type=click.Choice([v.value for v in RemoteVerbosity], case_sensitive=False),
            help="Remote machine verbosity",
            envvar="PROV_REMOTE_VERBOSITY",
            cls=GroupedOption,
            group=REMOTE_EXECUTION_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_REMOTE_DRY_RUN}",
            default=False,
            is_flag=True,
            show_default=True,
            help="Run command as NO-OP on remote machine, print commands to output, do not execute",
            envvar="PROV_REMOTE_DRY_RUN",
            cls=GroupedOption,
            group=REMOTE_EXECUTION_OPTS_GROUP_NAME,
        )
        @wraps(func)
        @click.pass_context  # Decorator to pass context to the function
        def wrapper(ctx, *args: Any, **kwargs: Any) -> Any:
            verbosity = kwargs.pop(normalize_cli_item(REMOTE_OPT_VERBOSITY))
            remote_verbosity = RemoteVerbosity.from_str(verbosity)

            dry_run = kwargs.pop(normalize_cli_item(REMOTE_OPT_REMOTE_DRY_RUN), False)
            remote_context = RemoteContext.create(
                dry_run=dry_run,
                verbose=remote_verbosity == RemoteVerbosity.Verbose,
                silent=remote_verbosity == RemoteVerbosity.Silent,
            )

            # Fail if environment is not supplied
            cli_flag_env = kwargs.pop(normalize_cli_item(REMOTE_OPT_ENV))
            environment = RunEnvironment.from_str(cli_flag_env)

            # Fail if connect-mode is not supplied
            cli_flag_conn_mode = kwargs.pop(normalize_cli_item(REMOTE_OPT_CONNECT_MODE))
            connect_mode = RemoteConnectMode.from_str(cli_flag_conn_mode)

            node_username = kwargs.pop(normalize_cli_item(REMOTE_OPT_NODE_USERNAME), None)
            node_password = kwargs.pop(normalize_cli_item(REMOTE_OPT_NODE_PASSWORD), None)
            ssh_private_key_file_path = kwargs.pop(normalize_cli_item(REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH), None)
            ip_discovery_range = kwargs.pop(normalize_cli_item(REMOTE_OPT_IP_DISCOVERY_RANGE), None)
            ip_address = kwargs.pop(normalize_cli_item(REMOTE_OPT_IP_ADDRESS), None)
            port = kwargs.pop(normalize_cli_item(REMOTE_OPT_PORT), None)
            hostname = kwargs.pop(normalize_cli_item(REMOTE_OPT_HOSTNAME), None)

            # Add it to the context object
            if ctx.obj is None:
                ctx.obj = {}

            if REMOTE_CLICK_CTX_NAME not in ctx.obj:
                # First-time initialization
                ctx.obj[REMOTE_CLICK_CTX_NAME] = RemoteOpts(
                    environment=environment,
                    connect_mode=connect_mode,
                    remote_context=remote_context,
                    conn_flags=RemoteOptsFromConnFlags(
                        node_username=node_username,
                        node_password=node_password,
                        ssh_private_key_file_path=ssh_private_key_file_path,
                        ip_address=ip_address,
                        port=port,
                        hostname=hostname,
                    ),
                    scan_flags=RemoteOptsFromScanFlags(ip_discovery_range=ip_discovery_range),
                    config=RemoteOptsFromConfig(remote_config=remote_config),
                )
                logger.debug("Initialized CliRemoteOpts for the first time.")
            else:
                # Update only the relevant fields if they change
                remote_opts = ctx.obj[REMOTE_CLICK_CTX_NAME]

                if verbosity and not remote_opts._remote_context._dry_run:
                    remote_opts._remote_context._dry_run = dry_run

                if verbosity and not remote_opts._remote_context._verbose:
                    remote_opts._remote_context._verbose = remote_verbosity == RemoteVerbosity.Verbose

                if verbosity and not remote_opts._remote_context._silent:
                    remote_opts._remote_context._silent = remote_verbosity == RemoteVerbosity.Silent

                if environment and remote_opts._environment != environment:
                    remote_opts._environment = environment

                if connect_mode and remote_opts._connect_mode != connect_mode:
                    remote_opts._connect_mode = connect_mode

                if node_username and remote_opts._flags.node_username != node_username:
                    remote_opts._flags.node_username = node_username

                if node_password and remote_opts._flags.node_password != node_password:
                    remote_opts._flags.node_password = node_password

                if (
                    ssh_private_key_file_path
                    and remote_opts._flags.ssh_private_key_file_path != ssh_private_key_file_path
                ):
                    remote_opts._flags.ssh_private_key_file_path = ssh_private_key_file_path

                if ip_address and remote_opts._flags.ip_address != ip_address:
                    remote_opts._flags.ip_address = ip_address

                if port and remote_opts._flags.port != port:
                    remote_opts._flags.port = port

                if hostname and remote_opts._flags.hostname != hostname:
                    remote_opts._flags.hostname = hostname

                if ip_discovery_range and remote_opts._scan_flags.ip_discovery_range != ip_discovery_range:
                    remote_opts._scan_flags.ip_discovery_range = ip_discovery_range

            return func(*args, **kwargs)

        return wrapper

    return decorator_without_params
