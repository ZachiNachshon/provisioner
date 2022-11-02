#!/usr/bin/env python3

import os
from typing import List, Optional

import typer
from loguru import logger
from common.anchor.anchor_runner import RunEnvironment
from common.remote.remote_connector import RemoteCliArgs

from config.config_resolver import ConfigResolver
from config.typer_remote_opts import TyperRemoteOpts
from example.dummy.anchor_cmd import AnchorCmd, AnchorCmdArgs
from example.dummy.installer_cmd import UtilityInstallerCmd, UtilityInstallerCmdArgs
from example.dummy.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs
from external.python_scripts_lib.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.python_scripts_lib.cli.typer_callbacks import collect_typer_options_into_list
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import (
    CliContextManager,
)

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "example/config.yaml"

ConfigResolver.resolve(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH)
TyperRemoteOpts.load(ConfigResolver.config)

dummy_cli_app = typer.Typer()


@dummy_cli_app.command(name="hello")
@logger.catch(reraise=True)
def hello(
    username: str = typer.Option(
        "Zachi Nachshon", help="User name to greet with hello world", envvar="DUMMY_HELLO_USERNAME"
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Run a dummy hello world scenario locally or on remote machine via Ansible playbook
    """
    try:
        args = HelloWorldCmdArgs(
            username=username,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts)
        )
        args.print()
        HelloWorldCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", e.__class__.__name__, str(e))


@dummy_cli_app.command(name="anchor")
@logger.catch(reraise=True)
def anchor(
    anchor_run_command: str = typer.Option(
        ...,
        show_default=False,
        help="Anchor run command (<cmd-name> run <category> --action=do-something)",
        envvar="ANCHOR_RUN_COMMAND",
    ),
    github_organization: str = typer.Option(
        None, show_default=False, help="GitHub repository organization", envvar="GITHUB_REPO_ORGANIZATION"
    ),
    repository_name: str = typer.Option(None, show_default=False, help="Repository name", envvar="ANCHOR_REPO_NAME"),
    branch_name: str = typer.Option("master", help="Repository branch name", envvar="ANCHOR_REPO_BRANCH_NAME"),
    git_access_token: str = typer.Option(
        ConfigResolver.get_config().anchor.github.github_access_token,
        help="GitHub access token (only for private repos)",
        envvar="GITHUB_ACCESS_TOKEN",
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Run a dummy anchor run scenario locally or on remote machine via Ansible playbook
    """
    try:
        args = AnchorCmdArgs(
            anchor_run_command=anchor_run_command,
            github_organization=github_organization,
            repository_name=repository_name,
            branch_name=branch_name,
            github_access_token=git_access_token,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts)
        )
        args.print()
        AnchorCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", e.__class__.__name__, str(e))

@dummy_cli_app.command(name="installer")
@logger.catch(reraise=True)
def installer(
    utility: List[str]= typer.Option(
        None,
        show_default=False,
        help="Specify a utility name or select from a list if none supplied (repeat as needed)",
        envvar="INSTALLER_UTILITIES",
    ),
    environment: RunEnvironment = typer.Option(
        None,
        show_default=False,
        help="Specify an environment or select from a list if none supplied",
        envvar="INSTALLER_ENVIRONMENT",
    ),
    github_access_token: str = typer.Option(
        ConfigResolver.get_config().anchor.github.github_access_token,
        show_default=False,
        help="GitHub access token for accessing installers private repo",
        envvar="GITHUB_ACCESS_TOKEN",
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Install locally or on a remote machine any utility by supplying its name or selecting it from a pre-defined list
    """
    try:
        # Wrap all --utility option into a single list
        utilities: Optional[List[str]] = collect_typer_options_into_list(utility)

        args = UtilityInstallerCmdArgs(
            utilities=utilities,
            environment=environment,
            github_access_token=github_access_token,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts)
        )
        args.print()
        UtilityInstallerCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to install utility. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to install utility. ex: {}, message: {}", e.__class__.__name__, str(e))