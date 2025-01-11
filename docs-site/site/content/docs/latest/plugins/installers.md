---
layout: docs
title: "Plugin: Installers"
description: Install anything anywhere on any OS/Arch either on a local or remote machine.
group: plugins
toc: true
---

## Overview

The installers plugin is designed to install any type of software, package, or application quickly and easily in a one-liner command.

Remove the hassle of going through multiple READMEs and/or documentation sites just to get the software installed.

{{< callout info >}}
**Important !** <br>
Installation can be performed either locally on the host machine or on a remote machine.

For local installations, an interactive flow will be initiated using a TUI (Terminal UI).
To install on a remote machine without triggering the interactive flow, use the Remote-Only flags to provide the remote machine details. Environment variables (ENV VARs) are also supported for this purpose.
{{< /callout >}}

## Quickstart

```text
# Interactive mode
$ provisioner plugins install

# Non interactive mode
$ pip install provisioner-installers-plugin
```

## Usage

Print a list of available installables

```bash
provisioner install 
```

{{< callout info >}}
Currently, the following installables are supported:
* CLI applications
* K3s server/agent
{{< /callout >}}

#### CLI

Install any supported CLI tool

```text
# List avaialble CLI installables 
$ provisioner install cli

# Install a specific installable
$ provisioner install cli <app-name>
```

#### K3s

K3s is fully compliant lightweight Kubernetes distribution (https://k3s.io).<br>
Provisioner allows installing either the k3s server or agent.

```text
# List avaialble k3s installables 
$ provisioner install k3s

# List avaialble CLI installables 
$ provisioner install k3s <server/agent>
```

## Remote Installation

When choosing a remote installation without an interactive flow, the necessary flags should be provided to allow the CLI command to run as a single-line command.

{{< bs-table >}}
| Remote Flag | Env Var | Description |
| --- | --- | --- |
| `--hostname` | `PROV_HOSTNAME` | Remote node host name |
| `--ip-address` | `PROV_IP_ADDRESS` | Remote node IP address |
| `--node-username` | `PROV_NODE_USERNAME` | Remote node username |
| `--node-password` | `PROV_NODE_PASSWORD` | (Optional) Remote node password |
| `--ssh-private-key-file-path` | `PROV_SSH_PRIVATE_KEY_FILE_PATH` | (Recommended) Private SSH key local file path |
{{< /bs-table >}}

Example:

```text
# Using CLI flags
provisioner install \
  --environment Remote \
  --hostname rpi-01 \
  --ip-address 1.2.3.4 \
  --node-username pi \
  --ssh-private-key-file-path /path/to/pkey \
  cli helm

# Using Env Vars 
PROV_HOSTNAME=rpi-01 \
PROV_IP_ADDRESS=1.2.3.4 \
PROV_NODE_USERNAME=pi \
PROV_SSH_PRIVATE_KEY_FILE_PATH=/path/to/pkey \
provisioner install --environment Remote cli helm
```