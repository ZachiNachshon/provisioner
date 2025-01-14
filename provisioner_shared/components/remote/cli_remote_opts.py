#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Optional

import click
from loguru import logger

from components.remote.remote_opts import REMOTE_CLICK_CTX_NAME, CliRemoteOpts, RemoteVerbosity
from components.runtime.cli.menu_format import GroupedOption, get_nested_value, normalize_cli_item
from provisioner_shared.components.remote.domain.config import RemoteConfig, RunEnvironment
from provisioner_shared.components.runtime.cli.click_callbacks import mutually_exclusive_callback
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext

REMOTE_GENERAL_OPTS_GROUP_NAME = "General"
REMOTE_CON_OPTS_GROUP_NAME = "Connection"
REMOTE_DISCOVERY_OPTS_GROUP_NAME = "Discovery"
REMOTE_EXECUTION_OPTS_GROUP_NAME = "Execution"

REMOTE_OPT_ENV = "environment"
REMOTE_OPT_NODE_USERNAME = "node-username"
REMOTE_OPT_NODE_PASSWORD = "node-password"
REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH = "ssh-private-key-file-path"
REMOTE_OPT_IP_ADDRESS = "ip-address"
REMOTE_OPT_HOSTNAME = "hostname"
REMOTE_OPT_IP_DISCOVERY_RANGE = "ip-discovery-range"
REMOTE_OPT_VERBOSITY = "verbosity"
REMOTE_OPT_REMOTE_DRY_RUN = "remote-dry-run"
REMOTE_OPT_REMOTE_NON_INTERACTIVE = "remote-non-interactive"


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
            f"--{REMOTE_OPT_NODE_USERNAME}",
            show_default=False,
            help="Remote node username",
            envvar="PROV_NODE_USERNAME",
            cls=GroupedOption,
            group=REMOTE_CON_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_NODE_PASSWORD}",
            show_default=False,
            help="Remote node password",
            envvar="PROV_NODE_PASSWORD",
            cls=GroupedOption,
            group=REMOTE_CON_OPTS_GROUP_NAME,
            callback=mutually_exclusive_callback,
        )
        @click.option(
            f"--{REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH}",
            show_default=False,
            help="Private SSH key local file path",
            envvar="PROV_SSH_PRIVATE_KEY_FILE_PATH",
            cls=GroupedOption,
            group=REMOTE_CON_OPTS_GROUP_NAME,
            callback=mutually_exclusive_callback,
        )
        @click.option(
            f"--{REMOTE_OPT_IP_ADDRESS}",
            default="",
            help="Remote node IP address",
            envvar="PROV_IP_ADDRESS",
            cls=GroupedOption,
            group=REMOTE_CON_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_HOSTNAME}",
            default="",
            help="Remote node host name",
            envvar="PROV_HOSTNAME",
            cls=GroupedOption,
            group=REMOTE_CON_OPTS_GROUP_NAME,
        )
        @click.option(
            f"--{REMOTE_OPT_IP_DISCOVERY_RANGE}",
            default=from_cfg_ip_discovery_range,
            show_default=True,
            help="LAN network IP discovery scan range",
            envvar="PROV_IP_DISCOVERY_RANGE",
            cls=GroupedOption,
            group=REMOTE_DISCOVERY_OPTS_GROUP_NAME,
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
        @click.option(
            f"--{REMOTE_OPT_REMOTE_NON_INTERACTIVE}",
            default=False,
            is_flag=True,
            show_default=True,
            help="Turn off interactive prompts and outputs on remote machine",
            envvar="PROV_REMOTE_NON_INTERACTIVE",
            cls=GroupedOption,
            group=REMOTE_EXECUTION_OPTS_GROUP_NAME,
        )
        @wraps(func)
        @click.pass_context  # Decorator to pass context to the function
        def wrapper(ctx, *args: Any, **kwargs: Any) -> Any:
            verbosity = kwargs.pop(normalize_cli_item(REMOTE_OPT_VERBOSITY))
            remote_verbosity = RemoteVerbosity.from_str(verbosity)

            dry_run = kwargs.pop(normalize_cli_item(REMOTE_OPT_REMOTE_DRY_RUN), False)
            non_interactive = kwargs.pop(normalize_cli_item(REMOTE_OPT_REMOTE_NON_INTERACTIVE), False)
            remote_context = RemoteContext.create(
                dry_run=dry_run,
                verbose=remote_verbosity == RemoteVerbosity.Verbose,
                silent=remote_verbosity == RemoteVerbosity.Silent,
                non_interactive=non_interactive,
            )

            # Fail if environment is not supplied
            environment = kwargs.pop(normalize_cli_item(REMOTE_OPT_ENV))
            run_env = RunEnvironment.from_str(environment)

            node_username = kwargs.pop(normalize_cli_item(REMOTE_OPT_NODE_USERNAME), None)
            node_password = kwargs.pop(normalize_cli_item(REMOTE_OPT_NODE_PASSWORD), None)
            ssh_private_key_file_path = kwargs.pop(normalize_cli_item(REMOTE_OPT_SSH_PRIVATE_KEY_FILE_PATH), None)
            ip_discovery_range = kwargs.pop(normalize_cli_item(REMOTE_OPT_IP_DISCOVERY_RANGE), None)
            ip_address = kwargs.pop(normalize_cli_item(REMOTE_OPT_IP_ADDRESS), None)
            hostname = kwargs.pop(normalize_cli_item(REMOTE_OPT_HOSTNAME), None)

            remote_hosts = remote_config.to_hosts_dict()

            # Add it to the context object
            if ctx.obj is None:
                ctx.obj = {}

            if REMOTE_CLICK_CTX_NAME not in ctx.obj:
                # First-time initialization
                ctx.obj[REMOTE_CLICK_CTX_NAME] = CliRemoteOpts(
                    environment,
                    node_username,
                    node_password,
                    ssh_private_key_file_path,
                    ip_discovery_range,
                    ip_address,
                    hostname,
                    remote_hosts,
                    remote_context,
                )
                logger.debug("Initialized CliRemoteOpts for the first time.")
            else:
                # Update only the relevant fields if they change
                remote_opts = ctx.obj[REMOTE_CLICK_CTX_NAME]

                if verbosity and not remote_opts.verbosity:
                    remote_opts.verbosity = True

                if dry_run and not remote_opts.dry_run:
                    remote_opts.dry_run = True

                if non_interactive and not remote_opts.non_interactive:
                    remote_opts.non_interactive = True

                if remote_context and remote_opts.remote_context != remote_context:
                    remote_opts.remote_context = remote_context

                if run_env and remote_opts.environment != run_env:
                    remote_opts.environment = run_env

                if node_username and remote_opts.node_username != node_username:
                    remote_opts.node_username = node_username

                if node_password and remote_opts.node_password != node_password:
                    remote_opts.node_password = node_password

                if ssh_private_key_file_path and remote_opts.ssh_private_key_file_path != ssh_private_key_file_path:
                    remote_opts.ssh_private_key_file_path = ssh_private_key_file_path

                if ip_discovery_range and remote_opts.ip_discovery_range != ip_discovery_range:
                    remote_opts.ip_discovery_range = ip_discovery_range

                if ip_address and remote_opts.ip_address != ip_address:
                    remote_opts.ip_address = ip_address

                if hostname and remote_opts.hostname != hostname:
                    remote_opts.hostname = hostname

            return func(*args, **kwargs)

        return wrapper

    return decorator_without_params
