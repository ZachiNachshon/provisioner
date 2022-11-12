#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger

from provisioner.common.anchor.anchor_runner import (
    AnchorCmdRunner,
    AnchorCmdRunnerCollaborators,
    AnchorRunnerCmdArgs,
    RunEnvironment,
)
from provisioner.common.remote.remote_connector import (
    RemoteCliArgs,
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.domain.serialize import (
    SerializationBase,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.errors.cli_errors import (
    InstallerUtilityNotSupported,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.context import Context
from provisioner.external.python_scripts_lib.python_scripts_lib.infra.evaluator import Evaluator
from provisioner.external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    AnsibleRunner,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.checks import Checks
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.json_util import JsonUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.network import NetworkUtil
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.process import Process
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import (
    ProgressIndicator,
)
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter
from provisioner.external.python_scripts_lib.python_scripts_lib.utils.summary import Summary

InstallablesJsonFilePath = "common/installer/installables.json"


class Installables(SerializationBase):
    class InstallableUtility:
        name: str

        def __init__(self, name: str) -> None:
            self.name = name

    def _parse_utilities_block(self, utilities_block: dict):
        for utility in utilities_block:
            if "name" in utility:
                u_obj = Installables.InstallableUtility(name=utility["name"])
                self.utilities[utility["name"]] = u_obj
            else:
                print("Bad utility configuration, please check JSON file. name: installables.json")

    def _try_parse_config(self, dict_obj: dict):
        if "utilities" in dict_obj:
            self.utilities = {}
            self._parse_utilities_block(dict_obj["utilities"])

    utilities: dict[str, InstallableUtility] = None


class UtilityInstallerRunnerCmdArgs:

    utilities: List[str]
    github_access_token: str
    remote_args: RemoteCliArgs

    def __init__(self, utilities: List[str], github_access_token: str, remote_args: RemoteCliArgs) -> None:

        self.utilities = utilities
        self.github_access_token = github_access_token
        self.remote_args = remote_args


class Collaborators:
    io: IOUtils
    checks: Checks
    json_util: JsonUtil
    summary: Summary
    prompter: Prompter
    printer: Printer
    process: Process
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class UtilityInstallerCmdRunnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.json_util = JsonUtil.create(ctx, self.io)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)
        self.summary = Summary.create(ctx, self.json_util, self.printer, self.prompter)


class UtilityInstallerCmdRunner:
    def run(
        self,
        ctx: Context,
        args: UtilityInstallerRunnerCmdArgs,
        collaborators: Collaborators,
        run_env: Optional[RunEnvironment] = None,
    ) -> None:

        logger.debug("Inside UtilityInstallerCmdRunner run()")

        collaborators.printer.print_with_rich_table_fn(generate_installer_welcome())

        utilities_to_install = Evaluator.eval_size_else_throws(
            call=lambda: self._resolve_utilities_to_install(collaborators.json_util, collaborators.prompter, args),
            ctx=ctx,
            err_msg="No utilities were resolved",
        )
        collaborators.summary.add_values("utilities", utilities_to_install)

        selected_run_env = Evaluator.eval_step_failure_throws(
            call=lambda: self._resolve_run_environment(run_env, collaborators.prompter),
            ctx=ctx,
            err_msg="Could not resolve run environment",
        )
        collaborators.summary.add_value("run_env", selected_run_env)

        remote_connector = None
        ssh_conn_info = None
        if selected_run_env == RunEnvironment.Remote:
            remote_connector = RemoteMachineConnector(
                collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
            )
            ssh_conn_info = Evaluator.eval_step_failure_throws(
                call=lambda: remote_connector.collect_ssh_connection_info(ctx, args.remote_args),
                ctx=ctx,
                err_msg="Could not resolve SSH connection info",
            )
            collaborators.summary.add_values("ssh_conn_info", ssh_conn_info)

        anchor_cols = AnchorCmdRunnerCollaborators(ctx)
        for utility in utilities_to_install:
            collaborators.printer.new_line_fn()
            collaborators.printer.print_horizontal_line_fn(f"Installing Utility: {utility.name}")
            collaborators.printer.print_fn(collaborators.summary.get_text())
            if not ctx.is_auto_prompt():
                collaborators.printer.new_line_fn()
                collaborators.prompter.prompt_for_enter_fn()

            AnchorCmdRunner().run(
                ctx,
                AnchorRunnerCmdArgs(
                    anchor_run_command=f"installer run {utility.name} --action=install",
                    github_organization="ZachiNachshon",
                    repository_name="shell-installers",
                    branch_name="master",
                    github_access_token=args.github_access_token,
                    remote_args=args.remote_args,
                ),
                collaborators=anchor_cols,
                run_env=selected_run_env,
                ssh_conn_info=ssh_conn_info,
            )

    def _resolve_utilities_to_install(
        self, json_util: JsonUtil, prompter: Prompter, args: UtilityInstallerRunnerCmdArgs
    ) -> List[Installables.InstallableUtility]:
        """
        If user supplied unstallable utilities names as CLI arguments, verify they are supported.
        Otherwise, prompt user to select one/many available installable utilities.
        """
        utilities_to_install: List[Installables.InstallableUtility] = []
        installables = self.read_installables(json_util)
        if args.utilities and len(args.utilities) > 0:
            utilities_to_install = self._verify_utilities_choice(installables, args.utilities)
        else:
            utilities_to_install = self._start_utility_selection(installables, prompter)
        return utilities_to_install

    def read_installables(self, json_util: JsonUtil) -> Installables:
        return json_util.read_file_fn(file_path=InstallablesJsonFilePath, class_name=Installables)

    def _verify_utilities_choice(
        self, installables: Installables, utilities_names: List[str]
    ) -> List[Installables.InstallableUtility]:
        result: List[Installables.InstallableUtility] = []
        for utility_name in utilities_names:
            if utility_name not in installables.utilities:
                raise InstallerUtilityNotSupported(f"name: {utility_name}")
            result.append(installables.utilities[utility_name])

        return result

    def _start_utility_selection(
        self, installables: Installables, prompter: Prompter
    ) -> List[Installables.InstallableUtility]:
        options_list: List[str] = []
        for key in installables.utilities.keys():
            options_list.append(key)
        selected_utilities: dict = prompter.prompt_user_multi_selection_fn(
            message="Please choose utilities", options=options_list
        )

        result: List[Installables.InstallableUtility] = []
        for utility_name in selected_utilities:
            if utility_name in installables.utilities:
                result.append(installables.utilities[utility_name])

        return result

    def _resolve_run_environment(self, run_env: RunEnvironment, prompter: Prompter) -> RunEnvironment:
        if run_env:
            return run_env

        options_dict: List[str] = ["Local", "Remote"]
        selected_scanned_item: dict = prompter.prompt_user_selection_fn(
            message="Please choose an environment", options=options_dict
        )
        if selected_scanned_item == "Local":
            return RunEnvironment.Local
        elif selected_scanned_item == "Remote":
            return RunEnvironment.Remote
        return None


def generate_installer_welcome() -> str:
    return f"""
  Choose one or more utilities to install either locally or on a remote machine.

  Upon selection you will be prompt to select a local/remote installation.
  When opting-in for the remote option you will be prompted for additional arguments.
"""


def generate_plan_before_install(
    utilities_to_install: List[Installables.InstallableUtility],
    selected_run_env: RunEnvironment,
    ssh_conn_info: SSHConnectionInfo,
) -> str:

    utils_format = ""
    if utilities_to_install:
        for utility in utilities_to_install:
            utils_format += f"  - {utility.name}\n"

    return f"""
Run environment:
  - {selected_run_env}

Utilities to install:
{utils_format}

"""
