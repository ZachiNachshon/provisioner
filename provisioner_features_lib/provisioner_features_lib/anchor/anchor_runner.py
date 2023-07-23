#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from python_core_lib.errors.cli_errors import MissingCliArgument
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.runner.ansible.ansible_runner import AnsibleHost, AnsiblePlaybook
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks

from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.remote_connector import RemoteMachineConnector
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts

ANSIBLE_PLAYBOOK_ANCHOR_RUN = """
---
- name: Anchor run command
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/anchor
      tags: ['anchor_run']
"""


class AnchorRunnerCmdArgs:

    anchor_run_command: str
    github_organization: str
    repository_name: str
    branch_name: str
    git_access_token: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        anchor_run_command: str,
        github_organization: str,
        repository_name: str,
        branch_name: str,
        git_access_token: str,
        remote_opts: Optional[CliRemoteOpts] = None,
    ) -> None:
        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.git_access_token = git_access_token
        self.remote_opts = remote_opts


class AnchorCmdRunner:
    def run(
        self,
        ctx: Context,
        args: AnchorRunnerCmdArgs,
        collaborators: CoreCollaborators,
    ) -> None:

        logger.debug("Inside AnchorCmdRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks())

        if args.remote_opts.environment == RunEnvironment.Local:
            self._start_local_run_command_flow(ctx, args, collaborators)
        elif args.remote_opts.environment == RunEnvironment.Remote:
            self._start_remote_run_command_flow(ctx, args, collaborators)
        else:
            raise MissingCliArgument("Missing Cli argument. name: environment")

    def _start_remote_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: CoreCollaborators):
        remote_connector = RemoteMachineConnector(collaborators)
        ssh_conn_info = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: remote_connector.collect_ssh_connection_info(ctx, args.remote_opts),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append(attribute_name="ssh_conn_info", value=ssh_conn_info)

        collaborators.printer().new_line_fn()
        output = collaborators.printer().progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                selected_hosts=ssh_conn_info.ansible_hosts,
                playbook=AnsiblePlaybook(
                    name="anchor_run",
                    content=ANSIBLE_PLAYBOOK_ANCHOR_RUN,
                    remote_context=args.remote_opts.get_remote_context(),
                ),
                ansible_vars=[
                    "anchor_command=Run",
                    f"\"anchor_args='{args.anchor_run_command}'\"",
                    f"anchor_github_organization={args.github_organization}",
                    f"anchor_github_repository={args.repository_name}",
                    f"anchor_github_repo_branch={args.branch_name}",
                    f"git_access_token={args.git_access_token}",
                ],
                ansible_tags=["anchor_run"],
            ),
            desc_run="Running Ansible playbook (Anchor Run)",
            desc_end="Ansible playbook finished (Anchor Run).",
        )

        collaborators.printer().new_line_fn().print_fn(output).print_with_rich_table_fn(
            generate_summary(
                ansible_hosts=ssh_conn_info.host_ip_pairs,
                anchor_cmd=args.anchor_run_command,
            )
        )

    def _start_local_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: CoreCollaborators):
        output = collaborators.process().run_fn(
            [f"anchor {args.anchor_run_command}"], allow_single_shell_command_str=True
        )
        collaborators.printer().print_fn(output)

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_summary(ansible_hosts: List[AnsibleHost], anchor_cmd: str):
    host_names = []
    ip_addresses = []
    if ansible_hosts and len(ansible_hosts) > 0:
        for host in ansible_hosts:
            host_names.append(host.host)
            ip_addresses.append(host.ip_address)
    return f"""
  You have successfully ran an Anchor command on the following remote machines:

    • Host Names.....: [yellow]{host_names}[/yellow]
    • IP Addresses...: [yellow]{ip_addresses}[/yellow]
    • Command........: [yellow]anchor {anchor_cmd}[/yellow]
"""
