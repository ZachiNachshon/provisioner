---
layout: docs
title: "Plugin: Single Board"
description: Single boards management as simple as it gets.
toc: true
group: plugins
---

## Overview

Manage small single-board computers such as Raspberry Pi using interactive commands.

Make the provisioning on such machines safe, secure and remotely possible, starting from the initial OS/Network set-up and configuration towards on-going maintenance.

## Quickstart

```bash
pip install provisioner-single-board-plugin
```

or, interactive plugin installation via:

```bash 
provisioner plugins install
```

## Usage

Print a list of available installables

```bash
provisioner single-board
```

{{< callout info >}}
Currently, supported single-boards are:
* Raspberry Pi
{{< /callout >}}

<br>

#### Raspberry Pi

The RPi basic set of commands are aimed to solve the pain of setting up and configuring a fresh RPi computer remotely:

* Burn a Raspbian OS image on SD-Card

  ```bash
  provisioner single-board raspberry-pi os burn-image
  ```

* Configure Raspbian OS software and hardware settings for an optimal headless computer to be used as a Kubernetes cluster master/node

  ```bash
  provisioner single-board raspberry-pi node configure
  ```

* Auto scan local network to identify the RPi computer once connected to the home network, allows to define a static IP address and re-connect it to the network with the new address

  ```bash
  provisioner single-board raspberry-pi node network
  ```
