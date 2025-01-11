#!/usr/bin/env python3

from enum import EnumType
from functools import wraps
from typing import Any, Callable, Optional

import click
from components.remote.remote_opts import CliRemoteOpts, RemoteVerbosity
from components.runtime.cli.menu_format import GroupedOption

from provisioner_shared.components.remote.domain.config import RemoteConfig, RunEnvironment
from provisioner_shared.components.runtime.cli.state import CliGlobalArgs
from provisioner_shared.components.runtime.infra.log import LoggerManager
from provisioner_shared.components.runtime.cli.click_callbacks import mutually_exclusive_callback
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext


# Define modifiers globally
def cli_remote_opts(remote_config: Optional[RemoteConfig] = None) -> Callable:
    from_cfg_ip_discovery_range = None
    if (remote_config is not None
        and hasattr(remote_config, "lan_scan")
        and hasattr(remote_config.lan_scan, "ip_discovery_range")
    ):
        from_cfg_ip_discovery_range = remote_config.lan_scan.ip_discovery_range

    # Important ! 
    # This is the actual click decorator, the signature is critical for click to work
    def decorator_without_params(func: Callable) -> Callable:
      @click.option(
          "--environment",
          default="Local",
          show_default=True,
          type=click.Choice([v.value for v in RunEnvironment], case_sensitive=False),
          help=f"Specify an environment",
          envvar="PROV_ENVIRONMENT",
          cls=GroupedOption, 
          group="Logging"
      )
      @click.option(
          "--node-username",
          show_default=False,
          help="Remote node username",
          envvar="PROV_NODE_USERNAME",
          cls=GroupedOption, 
          group="Connection Options"
      )
      @click.option(
          "--node-password",
          show_default=False,
          help="Remote node password",
          envvar="PROV_NODE_PASSWORD",
          cls=GroupedOption, 
          group="Connection Options",
          callback=mutually_exclusive_callback,
      )
      @click.option(
          "--ssh-private-key-file-path",
          show_default=False,
          help="Private SSH key local file path",
          envvar="PROV_SSH_PRIVATE_KEY_FILE_PATH",
          cls=GroupedOption, 
          group="Connection Options",
          callback=mutually_exclusive_callback,
      )
      @click.option(
          "--ip-address",
          default="",
          help="Remote node IP address",
          envvar="PROV_IP_ADDRESS",
          cls=GroupedOption, 
          group="Connection Options"
      )
      @click.option(
          "--hostname",
          default="",
          help="Remote node host name",
          envvar="PROV_HOSTNAME",
      )
      @click.option(
          "--ip-discovery-range",
          default=from_cfg_ip_discovery_range,
          help="LAN network IP discovery scan range",
          envvar="PROV_IP_DISCOVERY_RANGE",
          cls=GroupedOption, 
          group="Discovery Options"
      )
      @click.option(
          "--verbosity",
          default=RemoteVerbosity.Normal.value,
          show_default=True,
          type=click.Choice([v.value for v in RemoteVerbosity], case_sensitive=False),
          help=f"Remote machine verbosity",
          envvar="PROV_REMOTE_VERBOSITY",
          cls=GroupedOption, 
          group="Execution Options"
      )
      @click.option(
          "--remote-dry-run", "-rd",
          default=False,
          is_flag=True,
          show_default=True,
          help="[Remote Machine] Run command as NO-OP, print commands to output, do not execute",
          envvar="PROV_REMOTE_DRY_RUN",
          cls=GroupedOption, 
          group="Execution Options"
      )
      @click.option(
          "--remote-non-interactive", "-rn",
          default=False,
          is_flag=True,
          show_default=True,
          help="[Remote Machine] Turn off interactive prompts and outputs",
          envvar="PROV_REMOTE_NON_INTERACTIVE",
          cls=GroupedOption, 
          group="Execution Options"
      )
      @wraps(func)
      def wrapper(*args: Any, **kwargs: Any) -> Any:
        verbosity = kwargs.pop('verbosity')
        remote_verbosity = RemoteVerbosity.from_str(verbosity)

        dry_run = kwargs.pop('remote_dry_run', False)
        non_interactive = kwargs.pop('remote_non_interactive', False)
        remote_context = RemoteContext.create(
                dry_run=dry_run,
                verbose=remote_verbosity == RemoteVerbosity.Verbose,
                silent=remote_verbosity == RemoteVerbosity.Silent,
                non_interactive=non_interactive,
            )
          
        # Fail if environment is not supplied
        environment = kwargs.pop('environment')
        run_env = RunEnvironment.from_str(environment)

        node_username = kwargs.pop('node_username', None)
        node_password = kwargs.pop('node_password', None)
        ssh_private_key_file_path = kwargs.pop('ssh_private_key_file_path', None)
        ip_discovery_range = kwargs.pop('ip_discovery_range', None)
        ip_address = kwargs.pop('ip_address', None)
        hostname = kwargs.pop('hostname', None)

        remote_hosts=remote_config.to_hosts_dict()

        CliRemoteOpts.create(
          run_env, 
          node_username, 
          node_password, 
          ssh_private_key_file_path, 
          ip_discovery_range, 
          ip_address, 
          hostname, 
          remote_hosts,
          remote_context)
        
        return func(*args, **kwargs)
      
      return wrapper
    
    return decorator_without_params
