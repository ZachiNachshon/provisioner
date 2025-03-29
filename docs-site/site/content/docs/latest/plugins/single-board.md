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

Print a list of available single-board options:

```bash
provisioner single-board
```

{{< callout info >}}
Currently, the following single-boards are supported:
* Raspberry Pi
{{< /callout >}}

## Raspberry Pi

The Raspberry Pi commands address the challenges of setting up and configuring a fresh RPi computer remotely. This is especially useful for headless setups in IoT projects, Kubernetes clusters, or any scenario requiring remote management.

### Available Commands

```bash
provisioner single-board raspberry-pi --help
```

Currently, the following commands are available:

* `os burn-image` - Burn a Raspbian OS image on SD-Card
* `node configure` - Configure Raspbian OS software and hardware settings
* `node network` - Configure network settings including static IP address

### OS Commands

#### Burn Image

Burn a Raspbian OS image onto an SD card for use with your Raspberry Pi:

```bash
provisioner single-board raspberry-pi os burn-image
```

This interactive command will guide you through selecting:
1. The Raspbian OS image version
2. The target SD card device
3. Additional configuration options

### Node Commands

Node commands help you configure a Raspberry Pi that's already running Raspbian OS, either locally or remotely.

#### Configure Node

Configure Raspbian OS software and hardware settings to optimize a headless RPi computer:

```bash
provisioner single-board raspberry-pi node configure [OPTIONS]
```

**Common Options:**

```
--environment [Local|Remote]      Environment type (default: interactive)
--connect-mode [Interactive|Flags] Connection mode (default: interactive)
--node-username TEXT              Username for SSH connection
--node-password TEXT              Password for SSH connection
--ip-address TEXT                 IP address of the remote node
--port TEXT                       SSH port number
--hostname TEXT                   Hostname to set on the device
--verbosity [Normal|Verbose]      Output verbosity
-v, --verbose                     Enable verbose output
-y, --yes                         Auto-confirm prompts
```

**Advanced Configuration Options:**

```
--boot-behaviour [B1|B2|...]      Boot behavior (B1=CLI requiring login, etc.)
--ssh [0|1]                       SSH service (0=enabled, 1=disabled)
--camera [0|1]                    Camera interface (0=enabled, 1=disabled)
--spi [0|1]                       SPI interface (0=enabled, 1=disabled)
--i2c [0|1]                       I2C interface (0=enabled, 1=disabled)
--serial-bus [0|1]                Serial interface (0=enabled, 1=disabled)
```

#### Configure Network

Configure network settings on a Raspberry Pi, including setting a static IP address:

```bash
provisioner single-board raspberry-pi node network [OPTIONS]
```

**Common Options:**
```
--environment [Local|Remote]      Environment type (default: interactive)
--connect-mode [Interactive|Flags] Connection mode (default: interactive)
--node-username TEXT              Username for SSH connection
--node-password TEXT              Password for SSH connection
--ip-address TEXT                 IP address of the remote node
--port TEXT                       SSH port number
--hostname TEXT                   Hostname to set on the device
--verbosity [Normal|Verbose]      Output verbosity
-v, --verbose                     Enable verbose output
-y, --yes                         Auto-confirm prompts
```

**Network-specific Options:**
```
--static-ip-address TEXT          Static IP address to configure
--gw-ip-address TEXT              Gateway IP address (typically your router)
--dns-ip-address TEXT             DNS server address
--update-hosts-file               Update /etc/hosts with hostname and IP
--wifi-country TEXT               WiFi country code (e.g., US, UK, IL)
--wifi-ssid TEXT                  WiFi network name
--wifi-password TEXT              WiFi password
```

## Examples

### Remote Configuration

Configure a remote Raspberry Pi with optimized settings for headless operation:

```bash
provisioner single-board raspberry-pi node \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --node-password raspberry \
  --ip-address 192.168.1.100 \
  --port 22 \
  --hostname rpi-node1 \
  --verbose \
  configure \
  --boot-behaviour B1 \
  --ssh 0 \
  --camera 1 \
  --spi 1 \
  --i2c 1 \
  --serial-bus 1
```

### Network Configuration

Set up a static IP address on a remote Raspberry Pi:

```bash
provisioner single-board raspberry-pi node \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --node-password raspberry \
  --ip-address 192.168.1.100 \
  --port 22 \
  --hostname rpi-node1 \
  --verbose \
  network \
  --static-ip-address 192.168.1.200 \
  --gw-ip-address 192.168.1.1 \
  --dns-ip-address 192.168.1.1 \
  --update-hosts-file
```

## Environment Variables

You can use environment variables instead of command-line arguments:

| Environment Variable | Description |
|----------------------|-------------|
| `PROV_RPI_STATIC_IP` | Static IP address to set |
| `PROV_GATEWAY_ADDRESS` | Gateway/router IP address |
| `PROV_DNS_ADDRESS` | DNS server IP address |