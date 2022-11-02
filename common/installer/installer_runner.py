#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from common.anchor.anchor_runner import AnchorCmdRunner, AnchorCmdRunnerCollaborators, AnchorRunnerCmdArgs, RunEnvironment
from common.remote.remote_connector import RemoteCliArgs
from external.python_scripts_lib.python_scripts_lib.domain.serialize import SerializationBase
from external.python_scripts_lib.python_scripts_lib.errors.cli_errors import InstallerUtilityNotSupported

from external.python_scripts_lib.python_scripts_lib.infra.context import Context
from external.python_scripts_lib.python_scripts_lib.runner.ansible.ansible import (
    AnsibleRunner,
)
from external.python_scripts_lib.python_scripts_lib.utils.io_utils import IOUtils
from external.python_scripts_lib.python_scripts_lib.utils.json_util import JsonUtil
from external.python_scripts_lib.python_scripts_lib.utils.printer import Printer
from external.python_scripts_lib.python_scripts_lib.utils.progress_indicator import ProgressIndicator
from external.python_scripts_lib.python_scripts_lib.utils.prompter import Prompter
from external.python_scripts_lib.python_scripts_lib.utils.process import Process

InstallablesJsonFilePath= "common/installer/installables.json"

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

    def __init__(
        self,
        utilities: List[str],
        github_access_token: str,
        remote_args: RemoteCliArgs
    ) -> None:
    
        self.utilities = utilities
        self.github_access_token = github_access_token
        self.remote_args = remote_args


class Collaborators:
    io: IOUtils
    json_util: JsonUtil
    prompter: Prompter
    printer: Printer
    process: Process
    ansible_runner: AnsibleRunner


class UtilityInstallerCmdRunnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.json_util = JsonUtil.create(ctx, self.io)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)


class UtilityInstallerCmdRunner:
    def run(
        self, 
        ctx: Context, 
        args: UtilityInstallerRunnerCmdArgs, 
        collaborators: Collaborators,
        run_env: Optional[RunEnvironment] = None) -> None:

        logger.debug("Inside UtilityInstallerCmdRunner run()")

        collaborators.printer.print_with_rich_table_fn(generate_installer_welcome())
        utilities_to_install = self._resolve_utilities_to_install(collaborators.json_util, collaborators.prompter, args)

        selected_run_env=run_env
        if not run_env:
            selected_run_env = self._ask_for_run_environment(collaborators.prompter)
        if not selected_run_env:
            return


        # TODO: migrate local/remote env selection to here





        if run_env == RunEnvironment.Local:
            self._start_local_run_command_flow(ctx, args, collaborators)
        elif run_env == RunEnvironment.Remote:
            self._start_remote_run_command_flow(ctx, args, collaborators)
        else:
            return

        anchor_cols = AnchorCmdRunnerCollaborators(ctx)
        for utility in utilities_to_install:
            collaborators.printer.new_line_fn()
            collaborators.printer.print_with_rich_table_fn(f"Installing utility {utility.name}")
            if not ctx.is_auto_prompt():
                collaborators.prompter.prompt_for_enter_fn()

            AnchorCmdRunner().run(
                ctx, 
                AnchorRunnerCmdArgs(
                    anchor_run_command=f"installer run {utility.name} --action=install",
                    github_organization="ZachiNachshon",
                    repository_name="shell-installers",
                    branch_name="master",
                    github_access_token=args.github_access_token,
                    remote_args=args.remote_args
                ),
                collaborators=anchor_cols,
                run_env=selected_run_env
            )

    def _resolve_utilities_to_install(self, json_util: JsonUtil, prompter: Prompter, args: UtilityInstallerRunnerCmdArgs):
        utilities_to_install: List[Installables.InstallableUtility] = []
        installables = self.read_installables(json_util)
        if args.utilities and len(args.utilities) > 0:
            utilities_to_install = self._verify_utilities_choice(installables, args.utilities)
        else:
            utilities_to_install = self._start_utility_selection(installables, prompter)
        return utilities_to_install

    def is_user_specified_utilities(self, args: UtilityInstallerRunnerCmdArgs) -> bool:
        return 

    def read_installables(self, json_util: JsonUtil) -> Installables:
        return json_util.read_file_fn(file_path=InstallablesJsonFilePath, class_name=Installables)

    def _verify_utilities_choice(self, installables: Installables, utilities_names: List[str]) -> List[Installables.InstallableUtility]:
        result: List[Installables.InstallableUtility] = []
        for utility_name in utilities_names:
            if utility_name not in installables.utilities:
                raise InstallerUtilityNotSupported(f"name: {utility_name}")
            result.append(installables.utilities[utility_name])

        return result

    def _start_utility_selection(self, installables: Installables, prompter: Prompter) -> List[Installables.InstallableUtility]:
        options_list: List[str] = []
        for key in installables.utilities.keys():
            options_list.append(key)
        selected_utilities: dict = prompter.prompt_user_multi_selection_fn(
            message="Please choose utilities", options=options_list)

        result: List[Installables.InstallableUtility] = []
        for utility_name in selected_utilities:
            result.append(installables.utilities[utility_name])

        return result

    def _ask_for_run_environment(self, prompter: Prompter) -> RunEnvironment:
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
    return f"""Choose one or more utilities to install either locally or on a remote machine.

Upon selection you will be prompt to select a local/remote installation.
When opting-in for the remote option you will be prompted for additional arguments."""
