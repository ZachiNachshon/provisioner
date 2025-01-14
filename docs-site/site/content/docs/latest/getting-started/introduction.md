---
layout: docs
title: Get started with <code>provisioner</code>
description: Explore a variety of available CLI applications (also known as plugins), or create your own using a Python-based framework that supports the creation and dynamic loading of CLI applications at runtime
toc: true
aliases:
- "/docs/latest/getting-started/"
- "/docs/getting-started/"
- "/getting-started/"
---

## Requirements

- A Unix-like operating system: macOS, Linux
- Python `v3.11` and above

## QuickStart

The fastest way (for `macOS` and `Linux`) to install `provisioner` is from [PyPi](https://pypi.org/) via pip:

```bash
pip install provisioner-runtime
```

### Plugins

There are two methods used for plugins installation:

<br>

**Using Provisioner CLI:**

```text
# Interactive mode
$ provisioner plugins install

# Non interactive mode
$ provisioner plugins install --name provisioner-examples-plugin
```

**Using PyPi via pip:**

```text
# Examples plugin
$ pip install provisioner-examples-plugin

# Installers plugin
$ pip install provisioner-installers-plugin

# Single-Board plugin
$ pip install provisioner-single-board-plugin
```
