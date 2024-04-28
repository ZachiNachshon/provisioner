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
Installation can run either locally on the host machine or on a remote machine.<br>

When opting for remote machine, upon installation, an interactive flow will start using TUI (Terminal UI).<br>

To install on a remote machine without starting an interactive flow, `Remote-Only` flags should be used to supply the remote machine info (ENV VARs are also supported).
{{< /callout >}}

## Quickstart

```bash
pip install provisioner-installers-plugin
```

or, interactive plugin installation via:

```bash 
provisioner plugins install
```

## Usage

Print a list of available installables

```bash
provisioner install 
```

{{< callout info >}}
Currently, supported installables are:
* CLI applications
* K3s server/agent
{{< /callout >}}

#### CLI

Install any supported CLI tool

```bash
provisioner install cli <app-name>
```

#### K3s

K3s is fully compliant lightweight Kubernetes distribution (https://k3s.io).<br>
Provisioner allows installing either the k3s server or agent.

```bash
provisioner install k3s <server/agent>
```

## Remote Installation

When opting-in for a remote installation without an interactive flow, one should supply the required flags so the CLI command could run as a one-liner.

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

```bash
provisioner install \
  --environment Remote \
  --hostname rpi-01 \
  --ip-address 1.2.3.4 \
  --node-username pi \
  --ssh-private-key-file-path /path/to/pkey \
  cli helm
```

or

```bash
PROV_HOSTNAME=rpi-01 \
PROV_IP_ADDRESS=1.2.3.4 \
PROV_NODE_USERNAME=pi \
PROV_SSH_PRIVATE_KEY_FILE_PATH=/path/to/pkey \
provisioner install --environment Remote cli helm
```