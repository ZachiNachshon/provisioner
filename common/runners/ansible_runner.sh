#!/bin/bash

main() {
  local selected_hosts="localhost ansible_connection=local"

  # Working directory, usually the repository root absolute path
  local working_dir="$(pwd)"

  # Trigger the Ansible runner
  ./external/shell_scripts_lib/runner/ansible/ansible.sh \
    "username: pi" \
    "password: test" \
    "working_dir: ${working_dir}" \
    "selected_hosts: ${selected_hosts}" \
    "playbook_path: rpi/nodes/dummy.yaml" \
    "ansible_var: git_check=true" \
    "ansible_var: anchor_check=true" \
    "ansible_var: local_bin_folder=/zachi/path" \
    "ansible_var: rc_file_path=/zachi/rc/file" \
    "debug"
    # "playbook_path: external/ansible_playbooks/playbooks/check_utilities.yaml" \
    # "playbook_path: /usr/runner/workspace/external/ansible_playbooks/check_utilities/check_utilities.yaml" \
}

main "$@"