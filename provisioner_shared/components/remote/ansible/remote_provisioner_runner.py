#!/usr/bin/env python3

from typing import List

from loguru import logger

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.remote.remote_connector import SSHConnectionInfo

# Define the Ansible playbook template for running provisioner remotely
ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER = """
---
- name: Provisioner run command
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/provisioner
      tags: ['provisioner_wrapper']
"""

class RemoteProvisionerRunnerArgs:
    """Arguments for running provisioner commands remotely"""

    def __init__(
        self,
        provisioner_command: str,
        remote_context: RemoteContext,
        ssh_connection_info: SSHConnectionInfo,
        required_plugins: List[str] = None,
        install_method: str = "pip",
        ansible_tags: List[str] = None,
        ansible_vars: List[str] = None,
    ) -> None:
        """
        Initialize RemoteProvisionerRunnerArgs.
        
        Args:
            provisioner_command: The provisioner command to run on the remote machine
            remote_context: Context for remote execution
            ssh_connection_info: SSH connection information for the remote host
            required_plugins: List of required provisioner plugins
            install_method: Method to install provisioner ('pip' or 'github-release' or 'testing')
            ansible_tags: Additional Ansible tags to use
            ansible_vars: Additional Ansible variables to pass
        """
        self.provisioner_command = provisioner_command
        self.remote_context = remote_context
        self.ssh_connection_info = ssh_connection_info
        self.required_plugins = required_plugins or []
        self.install_method = install_method
        self.ansible_tags = ansible_tags or []
        self.ansible_vars = ansible_vars or []


class RemoteProvisionerRunner:
    """Utility class for running provisioner commands remotely via Ansible"""

    def run(self, ctx: Context, args: RemoteProvisionerRunnerArgs, collaborators: CoreCollaborators) -> str:
        logger.debug(f"Running provisioner command remotely: {args.provisioner_command}")
        
        return collaborators.progress_indicator().get_status().long_running_process_fn(
            call=lambda: self._execute_remote_ansible_provisioner_wrapper_playbook(
                ctx=ctx,
                args=args,
                collaborators=collaborators,
            ),
            desc_run="Running Ansible playbook remotely (Provisioner Wrapper)",
            desc_end="Ansible playbook finished remotely (Provisioner Wrapper).",
        )

    def _execute_remote_ansible_provisioner_wrapper_playbook(
        self, ctx: Context, args: RemoteProvisionerRunnerArgs, collaborators: CoreCollaborators
    ) -> str:
        """Execute the Ansible playbook that runs the provisioner command on remote machines."""
        runner = collaborators.ansible_runner()
        ansible_vars = self._prepare_ansible_vars(args, collaborators)
        ansible_tags = self._prepare_ansible_tags(args, collaborators)
        
        return runner.run_fn(
            selected_hosts=args.ssh_connection_info.ansible_hosts,
            playbook=AnsiblePlaybook(
                name="provisioner_wrapper",
                content=ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER,
                remote_context=args.remote_context,
            ),
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags,
        )

    def _prepare_ansible_tags(self, args: RemoteProvisionerRunnerArgs, collaborators: CoreCollaborators) -> List[str]:
        """Determine which Ansible tags to use."""
        ansible_tags = ["provisioner_wrapper"]
        
        if self._test_only_is_installer_run_from_local_sdists(collaborators):
            ansible_tags.append("provisioner_testing")
            
        ansible_tags.extend(args.ansible_tags)

        return ansible_tags
    
    def _prepare_ansible_vars(self, args: RemoteProvisionerRunnerArgs, collaborators: CoreCollaborators) -> List[str]:
        """Prepare Ansible variables for the remote execution."""
        # Log the exact command that will be executed remotely for debugging
        logger.debug(f"Remote provisioner command: {args.provisioner_command}")
        
        # Start with required vars
        ansible_vars = [
            f"provisioner_command='{args.provisioner_command}'",
            f"required_plugins={args.required_plugins}",
        ]
        
        # Add install method
        ansible_vars.append(f"install_method='{args.install_method}'")
        
        # Add any additional vars
        ansible_vars.extend(args.ansible_vars)

        # Add test vars if needed
        if self._test_only_is_installer_run_from_local_sdists(collaborators):
            test_vars = self._prepare_testing_ansible_vars(collaborators, args)
            ansible_vars.extend(test_vars)
        
        return ansible_vars 
    
    def _prepare_testing_ansible_vars(self, collaborators: CoreCollaborators, args: RemoteProvisionerRunnerArgs) -> List[str]:
        """Prepare Ansible variables for testing mode."""
        print("\n\n================================================================")
        print("\n===== Running Ansible Provisioner Wrapper in testing mode ======")
        print("\n================================================================\n")
        
        # Build sdists for testing
        temp_folder_path = self._test_only_prepare_test_artifacts(collaborators, args)
        
        # Return test-specific vars
        return [
            "install_method='testing'",
            "provisioner_testing=True",
            f"provisioner_e2e_tests_archives_host_path='{temp_folder_path}'",
            "ansible_python_interpreter='auto'"
        ]
        
    def _test_only_is_installer_run_from_local_sdists(self, collaborators: CoreCollaborators) -> bool:
        return collaborators.checks().is_env_var_equals_fn("PROVISIONER_INSTALLER_PLUGIN_TEST", "true")

    def _test_only_prepare_test_artifacts(self, collaborators: CoreCollaborators, args: RemoteProvisionerRunnerArgs) -> str:
        project_git_root = collaborators.io_utils().find_git_repo_root_abs_path_fn(clazz=RemoteProvisionerRunner)
        sdist_output_path = f"{project_git_root}/tests-outputs/provisioner-wrapper-plugins/dist"
        sdist_input_paths = [
            f"{project_git_root}/provisioner",
            f"{project_git_root}/provisioner_shared",
        ]
        
        for plugin in args.required_plugins:
            sdist_input_paths.append(f"{project_git_root}/plugins/{plugin}")

        collaborators.package_loader().build_sdists_fn(
            sdist_input_paths,
            sdist_output_path,
        )
        return sdist_output_path