#!/bin/bash
# K3s Information Gathering Script
#
# This script collects and displays information about a K3s installation
# on the local system, including service status, configuration details,
# and connection information.

set -e  # Exit on error

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

# Source shell library if available
if [[ -f "${SHELL_SCRIPTS_LIB_IMPORT_PATH}" ]]; then
    source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"
fi

LOCAL_BIN_FOLDER_PATH="${HOME}/.local/bin"
append_to_path "${LOCAL_BIN_FOLDER_PATH}"

#######################################
# Check if K3s service is running
# Outputs:
#   Service status to stdout
#######################################
function get_service_status() {
    systemctl is-active k3s.service 2>/dev/null || \
    systemctl is-active k3s-agent.service 2>/dev/null || \
    echo 'not installed'
}

#######################################
# Determine K3s node role (server, agent or none)
# Outputs:
#   Role to stdout
#######################################
function get_node_role() {
    if systemctl is-active k3s.service >/dev/null 2>&1; then
        echo "server"
    elif systemctl is-active k3s-agent.service >/dev/null 2>&1; then
        echo "agent"
    else
        echo "none"
    fi
}

#######################################
# Get K3s version
# Outputs:
#   Version to stdout
#######################################
function get_version() {
    k3s --version 2>/dev/null || echo 'not installed'
}

#######################################
# Find K3s config files
# Outputs:
#   Config paths to stdout
#######################################
function get_config_path() {
    find /etc/rancher/k3s/ -name '*.yaml' 2>/dev/null || echo 'no config found'
}

#######################################
# Find K3s token file path
# Outputs:
#   Token path to stdout
#######################################
function get_server_token_path() {
    if [[ -f "/var/lib/rancher/k3s/server/node-token" ]]; then
        echo '/var/lib/rancher/k3s/server/node-token'
    else
        echo 'not found'
    fi
}

#######################################
# Get K3s token value
# Outputs:
#   Token value to stdout
# Returns:
#   0 if token found, 1 if not
#######################################
function get_server_token() {
    local token_path="/var/lib/rancher/k3s/server/node-token"
    if [[ -f "${token_path}" ]]; then
        cat "${token_path}"
        return 0
    else
        echo 'not available'
        return 1
    fi
}

#######################################
# Get K3s agent token path
# Outputs:
#   Token path to stdout
#######################################
function get_agent_token_path() {
    local token_path="/etc/rancher/k3s/agent-token"
    if [[ -f "${token_path}" ]]; then
        echo "${token_path}"
    else
        echo 'not found'
    fi
}

#######################################
# Get K3s agent token value
# Outputs:
#   Token value to stdout
#######################################
function get_agent_token() {
    if [[ -f "/etc/rancher/k3s/agent-token" ]]; then
        echo '/etc/rancher/k3s/agent-token'
    else
        echo 'not found'
    fi
}

# Get K3s server URL from agent service
# Outputs:
#   Server URL to stdout
#######################################
function get_server_url() {
    local service_file="/etc/systemd/system/k3s-agent.service"
    if [[ -f "${service_file}" ]]; then
        local url=$(grep -o 'K3S_URL=[^ ]*' "${service_file}" | cut -d= -f2)
        if [[ -n "$url" ]]; then
            echo "$url"
        else
            # Use local IP if K3S_URL not found in service file
            local ip_address=$(hostname -I | awk '{print $1}')
            echo "https://${ip_address}:6443"
        fi
    else
        # Use local IP if service file doesn't exist
        local ip_address=$(hostname -I | awk '{print $1}')
        echo "https://${ip_address}:6443"
    fi
}

#######################################
# Get K3s command line arguments
# Outputs:
#   Command line args to stdout
#######################################
function get_cli_args() {
    if [[ -f "/etc/systemd/system/k3s.service" ]]; then
        grep -o -- '--[^ ]*' /etc/systemd/system/k3s.service || echo 'none'
    elif [[ -f "/etc/systemd/system/k3s-agent.service" ]]; then
        grep -o -- '--[^ ]*' /etc/systemd/system/k3s-agent.service || echo 'none'
    else
        echo 'not applicable'
    fi
}

#######################################
# Get number of K3s nodes
# Outputs:
#   Node count to stdout
#######################################
function get_node_count() {
    if command -v kubectl >/dev/null 2>&1 && [[ -f "/etc/rancher/k3s/k3s.yaml" ]]; then
        KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl get nodes --no-headers 2>/dev/null | wc -l || echo 'unknown'
    else
        echo 'not available'
    fi
}

#######################################
# Print connection information for server nodes
# Arguments:
#   $1 - Node role
#   $2 - Node token
# Outputs:
#   Connection info to stdout
#######################################
function print_connection_info() {
    local role="$1"
    local token="$2"
    
    if [[ "${role}" == "server" && "${token}" != "not available" ]]; then
        echo
        echo "--- Connection Information ---"
        echo "To join an agent to this server, use:"
        local ip_address=$(hostname -I | awk '{print $1}')
        echo "--k3s-url https://${ip_address}:6443 --k3s-token ${token}"
    fi
}

#######################################
# Print debug information
#######################################
function print_debug_info() {
    echo 
    echo "--- Debug Information ---"
    echo "To read the server logs, use:"
    echo "systemctl status k3s.service or journalctl -u k3s.service"
    echo 
    echo "To read the agent logs, use:"
    echo "systemctl status k3s-agent.service or journalctl -u k3s-agent.service"
}

# Main function to collect and display K3s information
#######################################
function main() {
    echo "--- K3s Information ---"
    
    # Get and display service status
    local service_status=$(get_service_status)
    echo "K3s Service Status: ${service_status}"
    
    # Get and display node role
    local role=$(get_node_role)
    echo "K3s Role: ${role}"
    
    # Get and display version
    local version=$(get_version)
    echo "K3s Version: ${version}"
    
    # Get and display config path
    local config_path=$(get_config_path)
    echo "K3s Config Path: ${config_path}"
    
    # Get and display token path
    local server_token_path=$(get_server_token_path)
    echo "K3s Server Token Path: ${server_token_path}"
    
    # Get and display token
    local server_token=$(get_server_token)
    echo "K3s Server Token: ${server_token}"
    
    # Get and display token path
    local agent_token_path=$(get_agent_token_path)
    echo "K3s Agent Token Path: ${agent_token_path}"
    
    # Get and display token
    local agent_token=$(get_agent_token)
    echo "K3s Agent Token: ${agent_token}"

    # Get and display server URL
    local server_url=$(get_server_url)
    echo "K3s Server URL: ${server_url}"
    
    # Get and display CLI arguments
    local cli_args=$(get_cli_args)
    echo "K3s Args: ${cli_args}"
    
    # Get and display node count
    local node_count=$(get_node_count)
    echo "Node Count: ${node_count}"
    
    # Print connection info if applicable
    print_debug_info
    print_connection_info "${role}" "${server_token}"
}

# Execute main function
main
exit 0 