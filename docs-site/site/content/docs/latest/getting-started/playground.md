---
layout: docs
title: Interactive Playground
description: Explore <code>Provisioner</code> features through practical examples
group: getting-started
toc: true
---

## The Examples Plugin

The Examples plugin provides a safe, interactive environment to explore Provisioner's capabilities without making any system changes. It demonstrates the framework's user interface patterns, command structures, and interactive features.

## Getting Started

### Installation

First, install the Examples plugin:

```bash
pip install provisioner-examples-plugin
```

This plugin adds several demonstration commands to your Provisioner installation, all designed to be completely safe to run.

### Exploring Commands

After installation, explore the available example commands:

```bash
provisioner examples --help
```

You'll see several command groups:

- `ansible` - Demonstrates localhost Ansible integration patterns
- `anchor` - Interact with an OSS tool

## Running Example Commands

### Basic Ansible Example

Try the "hello" command to see a basic Ansible integration example:

```bash
provisioner examples ansible hello
```

This command simulates an Ansible execution without actually modifying your system. It demonstrates:

- Command parameter handling
- Execution workflow visualization
- Success/failure reporting

<!-- ### Interactive Demos

To experience Provisioner's interactive capabilities:

```bash
# TODO: Maybe add dummy commands to the examples plugin instead of a full blown RPi command
provisioner single-board raspberry-pi node configure
```

This command demonstrates:

- Dynamic menu generation
- User input handling
- Parameter validation
- Contextual help -->

## Using Dry Run Mode

Provisioner includes a powerful "dry run" mode that shows what a command would do without actually executing it. This is especially useful for understanding complex commands before running them.

To use dry run mode, add the `--dry-run` flag (or `-d` for short):

```bash
provisioner examples ansible hello --dry-run
```

For more detailed output, combine with the verbose flag:

```bash
provisioner examples ansible hello --dry-run --verbose
```

This will display:

- Command hierarchy and structure
- Parameter values and sources
- Mock execution steps
- Validation checks

{{< callout info >}}
Dry run mode is available for all Provisioner commands, not just examples. It's a safe way to explore commands in production environments before execution.
{{< /callout >}}

<!-- ## Experiment Safely

The Examples plugin is designed for experimentation and learning. Feel free to try different command combinations, flags, and options to understand how Provisioner's command system works.

Some interesting commands to try:

```bash
# TODO (Zachi): Implement the following examples:

# Try the remote execution simulation

# Explore the progress reporting features

# See how validation works
``` -->
