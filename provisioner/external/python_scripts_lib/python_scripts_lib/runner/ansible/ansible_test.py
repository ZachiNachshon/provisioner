#!/usr/bin/env python3

import os
import unittest

from ...errors.cli_errors import ExternalDependencyFileNotFound, InvalidAnsibleHostPair
from ...infra.context import Context
from ...utils.io_utils import IOUtils
from ...utils.io_utils_fakes import FakeIOUtils
from ...utils.process import Process
from .ansible import AnsibleRunner, HostIpPair


class AnsibleRunnerTestShould(unittest.TestCase):
    def test_run_ansible_mock_flow(self):
        ctx = Context.create(dry_run=True, verbose=True, auto_prompt=True)

        username = "test-user"
        password = "test-pass"
        working_dir = "/path/to/working/dir"
        selected_hosts = [HostIpPair("localhost", "ansible_connection=local")]
        playbook_path = "/path/to/playbook/folder"
        ansible_vars = ["key1=value1", "key2=value2"]
        force_dockerized = True

        ansible_runner = AnsibleRunner.create(ctx=ctx, io_utils=FakeIOUtils.create(ctx), process=Process.create(ctx))

        output = ansible_runner.run_fn(
            username=username,
            password=password,
            working_dir=working_dir,
            selected_hosts=selected_hosts,
            playbook_path=playbook_path,
            ansible_vars=ansible_vars,
            force_dockerized=force_dockerized,
        )

        self.assertIn(
            """sh \
./external/shell_scripts_lib/runner/ansible/ansible.sh \
working_dir: /path/to/working/dir \
username: test-user \
password: test-pass \
playbook_path: /path/to/playbook/folder \
selected_host: localhost ansible_connection=local \
ansible_var: key1=value1 \
ansible_var: key2=value2 \
--force-dockerized \
--dry-run \
--verbose""",
            output,
        )

    def test_run_ansible_mock_flow_custom_shell_runner(self):
        ctx = Context.create(dry_run=True, verbose=True, auto_prompt=True)
        ansible_shell_runner_path = "path/to/custom/ansible/shell/runner/ansible.sh"
        ansible_runner = AnsibleRunner.create(
            ctx=ctx,
            io_utils=FakeIOUtils.create(ctx),
            process=Process.create(ctx),
            ansible_shell_runner_path=ansible_shell_runner_path,
        )

        output = ansible_runner.run_fn(
            username="",
            password="",
            working_dir="",
            selected_hosts="",
            playbook_path="",
            ansible_vars="",
            force_dockerized="",
        )

        self.assertIn(
            f"sh ./{ansible_shell_runner_path}",
            output,
        )

    def test_run_ansible_fail_on_missing_shell_runner_path(self):
        ctx = Context.create(dry_run=False, verbose=True, auto_prompt=True)
        # Use real IOUtils to explicitly fail on missing Ansible shell runner
        ansible_runner = AnsibleRunner.create(
            ctx=ctx,
            io_utils=IOUtils.create(ctx),
            process=Process.create(ctx),
            ansible_shell_runner_path="/invalid/ansible/shell/runner/ansible.sh",
        )

        with self.assertRaises(ExternalDependencyFileNotFound):
            ansible_runner.run_fn(
                username="",
                password="",
                working_dir="",
                selected_hosts="",
                playbook_path="",
                ansible_vars="",
                force_dockerized="",
            )

    def test_run_ansible_fail_on_invalid_host_ip_pair(self):
        ctx = Context.create(dry_run=False, verbose=True, auto_prompt=True)
        ansible_runner = AnsibleRunner.create(
            ctx=ctx,
            io_utils=FakeIOUtils.create(ctx),
            process=Process.create(ctx),
        )

        with self.assertRaises(InvalidAnsibleHostPair):
            ansible_runner.run_fn(
                username="",
                password="",
                working_dir="",
                selected_hosts=[HostIpPair("localhost", None)],
                playbook_path="",
                ansible_vars="",
                force_dockerized="",
            )

    def test_integration_run_ansible_dry_run_flow(self):
        ctx = Context.create(dry_run=False, verbose=True, auto_prompt=True)
        ansible_ctx = Context.create(dry_run=True, verbose=True, auto_prompt=True)

        username = "test-user"
        password = "test-pass"
        working_dir = os.getcwd()
        selected_hosts = [HostIpPair("localhost", "ansible_connection=local")]
        playbook_path = "external/shell_scripts_lib/runner/ansible/test_data/test_playbook.yaml"
        ansible_vars = ["key1=value1", "key2=value2"]
        force_dockerized = False

        ansible_runner = AnsibleRunner.create(
            ctx=ansible_ctx, io_utils=IOUtils.create(ctx), process=Process.create(ctx)
        )

        output = ansible_runner.run_fn(
            username=username,
            password=password,
            working_dir=working_dir,
            selected_hosts=selected_hosts,
            playbook_path=playbook_path,
            ansible_vars=ansible_vars,
            force_dockerized=force_dockerized,
        )

        ansible_hosts_path = os.path.expanduser("~/.config/ansible/ansible_hosts")
        ansible_config_path = os.path.expanduser("~/.config/ansible/config")

        self.assertIn(
            """
[all:vars]
ansible_connection=ssh

# The RPi remote user (default: pi)
ansible_user=test-user

# Redundant if supplying the local SSH key path using SECRET_ANSIBLE_SSH_KEY_PATH in .secrets file
ansible_ssh_pass=test-pass

# These are the user selected hosts from the prompted selection menu
[selected_hosts]
localhost ansible_connection=local""",
            output,
        )

        # The first assertion checks that the shell_scripts_lib symlink was properly mounted as a docker volume.
        # The host path might vary depends on the running machine, this is the reason a regex assertion was used.
        # Symlinks used within a docker container MUST be mounted to the container as well, otherwise it won't be
        # possible to get their reallink
        self.assertRegex(output, f'docker run -v ".*":"/usr/runner/workspace/external/shell_scripts_lib"')

        # Rest of the assertions
        self.assertIn(f'-v "{ansible_hosts_path}":"/usr/runner/workspace/ansible_hosts"', output)
        self.assertIn(f'-v "{ansible_config_path}":"/usr/runner/workspace/config"', output)
        self.assertIn(f'-v "{working_dir}":"/usr/runner/workspace"', output)
        self.assertIn('-v "/var/run/docker.sock":"/var/run/docker.sock"', output)
        self.assertIn('-e VERBOSE="true"', output)
        self.assertIn("shell_runner/ansible", output)
        self.assertIn(
            f"-i /usr/runner/workspace/ansible_hosts -vvv {playbook_path} -e ansible_user={username} -e ansible_ssh_pass={password} -e local_bin_folder=/home/test-user/.local/bin -e  {ansible_vars[0]} -e  {ansible_vars[1]} ",
            output,
        )
