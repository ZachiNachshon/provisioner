---
layout: docs
title: "Plugin: Installers"
description: Install anything anywhere on any OS/Arch either on a local or remote machine.
group: plugins
toc: true
---

## Overview

The Installers plugin simplifies software installation with one-line commands, eliminating the need to navigate multiple documentation sources. It supports installing:

- CLI tools with specific version targeting
- K3s Kubernetes (server or agent)
- System packages and utilities

Installation can be performed either locally or on remote machines via SSH.

## Installation

```text
# Interactive mode
$ provisioner plugins install

# Non interactive mode
$ pip install provisioner-installers-plugin
```

## Usage

### List Available Installables

To see all installation options:

```bash
provisioner install
```

### Install CLI Tools

```bash
# List available CLI tools
provisioner install cli

# Install a CLI tool (latest version)
provisioner install cli helm

# Install a specific version
provisioner install cli helm@v3.14.1
```

<!-- Supported version formats:
- Specific version: `@v3.14.1`, `@3.14.1`, `@latest`
- Version constraints: `@^3.0.0` (any 3.x.x version) -->

### Install K3s

```bash
# List K3s installation options
provisioner install k3s

# Install K3s server
provisioner install k3s server

# Install K3s agent
provisioner install k3s agent
```

### Install System Packages

```bash
# List system package options
provisioner install system

# Install a specific package
provisioner install system docker
```

## Installation Modes

The plugin supports two installation modes:

### Interactive Mode (Default)

When run without additional flags, the plugin launches an interactive Terminal UI (TUI) that guides you through the installation process with step-by-step prompts.

```bash
provisioner install cli
```

### Non-Interactive Mode

For scripting or automation, you can specify all parameters directly:

```bash
provisioner install cli helm@v3.14.1
```

## Remote Installation

To install software on remote machines:

```text
# Basic syntax
provisioner install --environment Remote [options] COMMAND

# Example with explicit flags
provisioner install \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --ssh-private-key-file-path ~/.ssh/id_rsa \
  --ip-address 1.2.3.4 \
  --port 22 \
  --hostname rpi-01 \
  --verbosity Verbose \
  cli kubectl@v1.28.4
```

### Remote Configuration Options

| Remote Flag | Env Var | Description |
|-------------|---------|-------------|
| `--hostname` | `PROV_HOSTNAME` | Remote node hostname |
| `--ip-address` | `PROV_IP_ADDRESS` | Remote node IP address |
| `--node-username` | `PROV_NODE_USERNAME` | Remote node username |
| `--node-password` | `PROV_NODE_PASSWORD` | (Optional) Remote node password |
| `--ssh-private-key-file-path` | `PROV_SSH_PRIVATE_KEY_FILE_PATH` | (Recommended) SSH private key path |
| `--port` | `PROV_PORT` | SSH port (default: 22) |

### Using Environment Variables

You can use environment variables instead of flags:

```bash
PROV_NODE_USERNAME=admin \
PROV_SSH_PRIVATE_KEY_FILE_PATH=~/.ssh/id_rsa \
provisioner install --environment Remote cli helm@v3.11.0
```

## Additional Options

- `--dry-run (-d)` : Simulates command execution without making changes
- `--verbose (-v)` : Enables verbose logging

## Examples

### Install Latest `kubectl` Locally

```bash
provisioner install cli kubectl
```

### Install Specific `helm` Version Remotely

```bash
PROV_NODE_USERNAME=admin \
PROV_SSH_PRIVATE_KEY_FILE_PATH=~/.ssh/id_rsa \
provisioner install \
  --environment Remote \
  --connect-mode Flags \
  --ip-address 1.2.3.4 \
  --port 22 \
  --hostname rpi-01 \
  --verbosity Verbose \
  cli helm@v3.11.2
```

### Deploy `k3s` Server to Remote Machine

```bash
provisioner install \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --ssh-private-key-file-path ~/.ssh/id_rsa \
  --ip-address 1.2.3.4 \
  --port 22 \
  --hostname rpi-01 \
  --verbosity Verbose \
  k3s server
```