---
layout: docs
title: "Plugin: Examples"
description: Playground for using the CLI framework with basic dummy commands.
group: usage
toc: true
---

## Overview

The exampels plugin was introduced to allow users to experience the `provisioner` CLI in action on example dummy commands.

## Quickstart

```bash
pip install provisioner-examples-plugin
```

## Usage

Print a list of available examples

```bash
provisioner examples
```

{{< callout info >}}
Currently, supported examples are:
* Ansible
* Anchor
{{< /callout >}}

Run a no-op Ansible command

```bash
provisioner examples ansible hello
```

## Dry Run

Using `provisioner`, every command is a playground.

Use the `--dry-run` (short: `-d`) to check command exeuction breakdown, you can also add the `--verbose` (short: `-v`) flag to read DEBUG information.

*All dry-run actions are no-op, you can safely run them as they only print to stdout.*
