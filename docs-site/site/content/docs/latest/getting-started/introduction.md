---
layout: docs
title: Get Started with <code>Provisioner</code>
description: A modular CLI framework for creating and managing extensible command-line applications
toc: true
aliases:
- "/docs/latest/getting-started/"
- "/docs/getting-started/"
- "/getting-started/"
---

## Introduction

Provisioner is a Python-based framework for creating, managing, and executing modular command-line applications. Its plugin architecture allows teams to develop, share, and integrate specialized tools while maintaining a consistent user experience across all components.

## System Requirements

- **Operating System**: Unix-like systems (macOS, Linux)
- **Python**: Version 3.11 or higher
- **Disk Space**: Minimal (~5MB for core runtime, varies by plugins)
- **Additional Requirements**: Specific plugins may have additional dependencies

## Installation

### Installing the Core Runtime

The core runtime provides the foundation for all Provisioner functionality. Install it using pip:

```bash
pip install provisioner-runtime
```

After installation, verify the setup by running:

```bash
provisioner --version
```

### Installing Plugins

Plugins extend Provisioner's capabilities with specialized functionality. You can install plugins through two methods:

#### Method 1: Using the Provisioner CLI (Recommended)

This method leverages Provisioner's built-in plugin management:

```bash
# Interactive mode - presents a list of available plugins
provisioner plugins install

# Non-interactive mode - installs a specific plugin
provisioner plugins install --name provisioner-examples-plugin
```

#### Method 2: Direct Installation via pip

You can also install plugins directly using pip:

```bash
# Example plugin (for learning and experimentation)
pip install provisioner-examples-plugin

# Single-board plugin (for Raspberry Pi and other single-board computers)
pip install provisioner-single-board-plugin

# Installers plugin (for software installation utilities)
pip install provisioner-installers-plugin
```

## Basic Usage

### Exploring Available Commands

To see all available commands:

```bash
provisioner --help
```

To explore commands from a specific plugin:

```text
provisioner examples --help
provisioner single-board --help
```

### Command Structure

Provisioner uses a hierarchical command structure:

```
provisioner <plugin> <module> <submodule> [options] <command>
```

For example:

```bash
provisioner single-board raspberry-pi node configure
```

### Interactive vs. Non-Interactive Mode

Most commands support both interactive and non-interactive modes:

- **Interactive Mode**: Guides you through options with prompts and menus
- **Non-Interactive Mode**: Uses command-line flags for automation and scripting

Example of non-interactive mode:

```bash
provisioner single-board raspberry-pi node \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --ip-address 192.168.1.100 \
  network
```

## Next Steps

- Explore the [Playground](./playground.md) to try example commands
- Learn about the [Repository Structure](./repository-structure.md)
- Understand Provisioner's [design philosophy](./overview.md)
- Set up a [development environment](./development.md) to contribute or create your own plugins
