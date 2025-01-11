---
layout: docs
title: "Plugin: Examples"
description: Playground for using the CLI framework with basic dummy commands.
group: plugins
toc: true
---

## Overview

The examples plugin was created to let users experience the `provisioner` CLI in action through sample dummy commands.

## Quickstart

```text
# Interactive mode
$ provisioner plugins install

# Non interactive mode
$ pip install provisioner-examples-plugin
```

## Usage

Print a list of available examples

```bash
provisioner examples
```

{{< callout info >}}
Currently, the following examples are supported:
* Ansible
* Anchor
{{< /callout >}}

Run a no-op Ansible command

```bash
provisioner examples ansible hello
```
