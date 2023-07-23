#!/usr/bin/env python3

from typing import List, Optional

from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from python_core_lib.test_lib.assertions import to_json
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil


class FakeAnsibleRunnerLocal(AnsibleRunnerLocal):

    # Used to serialize objects to string for assertion error logs
    json_util: JsonUtil = None

    @staticmethod
    def calculate_hash(
        selected_hosts: List[AnsibleHost],
        playbook: AnsiblePlaybook,
        ansible_vars: List[str],
        ansible_tags: List[str],
    ) -> str:
        return hash((tuple(selected_hosts), playbook, tuple(ansible_vars), tuple(ansible_tags)))

    class FakeAnsibleCommandArgs:
        selected_hosts: List[AnsibleHost]
        playbook: AnsiblePlaybook
        ansible_vars: List[str]
        ansible_tags: List[str]

        def __init__(
            self,
            selected_hosts: List[AnsibleHost],
            playbook: AnsiblePlaybook,
            ansible_vars: Optional[List[str]] = None,
            ansible_tags: Optional[List[str]] = None,
        ) -> None:

            self.selected_hosts = selected_hosts
            self.playbook = playbook
            self.ansible_vars = ansible_vars
            self.ansible_tags = ansible_tags

        def __eq__(self, other):
            # print("=========== COMPARE ============")
            # print(f"this: " + str(self.__dict__))
            # print(f"that: " + str(other.__dict__))
            if isinstance(other, self.__class__):
                return hash(self) == hash(other)
            return False

        def __hash__(self):
            return FakeAnsibleRunnerLocal.calculate_hash(
                selected_hosts=self.selected_hosts,
                playbook=self.playbook,
                ansible_vars=self.ansible_vars,
                ansible_tags=self.ansible_tags,
            )

    registered_commands: List[FakeAnsibleCommandArgs] = []

    def __init__(self, ctx: Context) -> None:

        super().__init__(io_utils=None, paths=None, ctx=ctx)
        ctx = Context.create()
        self.json_util = JsonUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))

    @staticmethod
    def _create_fake(ctx: Context) -> "FakeAnsibleRunnerLocal":
        ansible_runner = FakeAnsibleRunnerLocal(ctx)
        ansible_runner.run_fn = (
            lambda selected_hosts, playbook, ansible_vars=None, ansible_tags=None: ansible_runner._record_command(
                selected_hosts=selected_hosts,
                playbook=playbook,
                ansible_vars=ansible_vars,
                ansible_tags=ansible_tags,
            )
        )
        return ansible_runner

    @staticmethod
    def create(ctx: Context) -> "FakeAnsibleRunnerLocal":
        return FakeAnsibleRunnerLocal._create_fake(ctx)

    def _record_command(
        self,
        selected_hosts: List[AnsibleHost],
        playbook: AnsiblePlaybook,
        ansible_vars: List[str],
        ansible_tags: List[str],
    ):
        self.registered_commands.append(
            FakeAnsibleRunnerLocal.FakeAnsibleCommandArgs(
                selected_hosts=selected_hosts,
                playbook=playbook,
                ansible_vars=ansible_vars,
                ansible_tags=ansible_tags,
            )
        )

    def assert_command(
        self,
        selected_hosts: List[AnsibleHost],
        playbook: AnsiblePlaybook,
        ansible_vars: List[str],
        ansible_tags: List[str],
    ) -> FakeAnsibleCommandArgs:

        cmd_args = FakeAnsibleRunnerLocal.FakeAnsibleCommandArgs(
            selected_hosts=selected_hosts,
            playbook=playbook,
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags,
        )
        if cmd_args not in self.registered_commands:
            cmd_args_json = self.json_util.to_json_fn(cmd_args)
            # print("===========")
            # print(to_json(self.registered_commands[0]))
            # print("===========")
            # print(str(cmd_args_json))
            # print("===========")
            raise FakeEnvironmentAssertionError(
                "Ansible command was not triggered with expected arguments. args:\n"
                + f"All registered commands:\n{to_json(self.registered_commands)}\n"
                + f"Expected command:\n{str(cmd_args_json)}"
            )
        return cmd_args
