---
layout: docs
title: "Plugin: Single Board"
description: Single boards management as simple as it gets.
toc: true
group: plugins
---

## Overview

Manage small single-board computers like Raspberry Pi using interactive commands.

Ensure that provisioning on these machines is safe, secure, and manageable remotely—from the initial OS and network setup to ongoing maintenance.

## Quickstart

```text
# Interactive mode
$ provisioner plugins install

# Non interactive mode
$ pip install provisioner-single-board-plugin
```

## Usage

Print a list of available installables

```bash
provisioner single-board
```

{{< callout info >}}
Currently, the following single-boards are supported:
* Raspberry Pi
{{< /callout >}}

<br>

#### Raspberry Pi

The basic set of RPi commands is designed to address the challenges of setting up and configuring a fresh RPi computer remotely:

* Burn a Raspbian OS image on SD-Card

  ```bash
  provisioner single-board raspberry-pi os burn-image
  ```

* Configure Raspbian OS software and hardware settings to optimize a headless RPi computer for use as a Kubernetes cluster master or node.

  ```bash
  provisioner single-board raspberry-pi node configure
  ```

* Automatically scan the local network to detect the RPi computer once connected to the home network. This allows you to define a static IP address and reconnect it with the new address.

  ```bash
  provisioner single-board raspberry-pi node network
  ```
