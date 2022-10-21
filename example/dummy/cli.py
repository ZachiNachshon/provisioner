#!/usr/bin/env python3

import os
from typing import Optional

import typer
from loguru import logger

from config.config_resolver import ConfigResolver
from config.typer_remote_opts import TyperRemoteOpts
from example.dummy.anchor_cmd import AnchorCmd, AnchorCmdArgs
from example.dummy.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs
from external.python_scripts_lib.python_scripts_lib.cli.state import CliGlobalArgs
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from external.python_scripts_lib.python_scripts_lib.infra.context import (
    CliContextManager,
)

CONFIG_USER_PATH = os.path.expanduser("~/.config/.provisioner/config.yaml")
CONFIG_INTERNAL_PATH = "rpi/config.yaml"

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
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Run a dummy hello world scenario locally or on remote machine via Ansible playbook
    """
    try:
        config = ConfigResolver.get_config()
        args = HelloWorldCmdArgs(
            username=username,
            node_username=node_username if node_username else config.node_username,
            node_password=node_password if node_username else config.node_password,
            ip_discovery_range=ip_discovery_range if ip_discovery_range else config.ip_discovery_range,
        )
        args.print()
        ctx = CliContextManager.create()
        HelloWorldCmd().run(ctx=ctx, args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


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
        ConfigResolver.get_config().active_system,
        help="GitHub access token (only for private repos)",
        envvar="GITHUB_ACCESS_TOKEN",
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Run a dummy run anchor scenario locally or on remote machine via Ansible playbook
    """
    try:
        config = ConfigResolver.get_config()
        args = AnchorCmdArgs(
            anchor_run_command=anchor_run_command,
            github_organization=github_organization,
            repository_name=repository_name,
            branch_name=branch_name,
            git_access_token=git_access_token,
            node_username=node_username if node_username else config.node_username,
            node_password=node_password if node_username else config.node_password,
            ip_discovery_range=ip_discovery_range if ip_discovery_range else config.ip_discovery_range,
        )
        args.print()
        ctx = CliContextManager.create()
        AnchorCmd().run(ctx=ctx, args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
