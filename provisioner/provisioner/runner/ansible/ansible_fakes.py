#!/usr/bin/env python3

from typing import List, Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.runner.ansible.ansible_runner import (
    ANSIBLE_PLAYBOOKS_PYTHON_PACKAGE,
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from provisioner.test_lib.faker import TestFakes


class FakeAnsibleRunnerLocal(TestFakes, AnsibleRunnerLocal):
    def __init__(self, ctx: Context) -> None:
        TestFakes.__init__(self)
        AnsibleRunnerLocal.__init__(self, io_utils=None, paths=None, ctx=ctx)

    @staticmethod
    def create(ctx: Context) -> "FakeAnsibleRunnerLocal":
        fake = FakeAnsibleRunnerLocal(ctx=ctx)
        fake.run_fn = MagicMock(side_effect=fake.run_fn)
        return fake

    def run_fn(
        self,
        selected_hosts: List[AnsibleHost],
        playbook: AnsiblePlaybook,
        ansible_vars: Optional[List[str]] = None,
        ansible_tags: Optional[List[str]] = None,
        ansible_playbook_package: Optional[str] = ANSIBLE_PLAYBOOKS_PYTHON_PACKAGE,
    ) -> str:
        return self.trigger_side_effect(
            "run_fn", selected_hosts, playbook, ansible_vars, ansible_tags, ansible_playbook_package
        )
