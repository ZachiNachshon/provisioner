#!/bin/bash

main() {
  local selected_hosts="localhost ansible_connection=local"

  # Working directory, usually the repository root absolute path
  local working_dir="$(pwd)/external/ansible_playbooks"

  # Trigger the Ansible runner
  ./external/shell_scripts_lib/runner/ansible/ansible.sh \
    "username: pi" \
    "password: test" \
    "working_dir: ${working_dir}" \
    "selected_hosts: ${selected_hosts}" \
    "playbook_name: check_utilities/check_utilities" \
    "ansible_var: git_check=true" \
    "ansible_var: anchor_check=false" \
    "debug"
}

main "$@"