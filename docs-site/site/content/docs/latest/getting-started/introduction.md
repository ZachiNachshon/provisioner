---
layout: docs
title: Get started with <code>provisioner</code>
description: Browse through a range of available CLI applications a.k.a plugins or create new ones using a Python based framework allowing for creation and loading of dynamic CLI applications at runtime.
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

There are two methods for plugins installation, from PyPi or interactively from provisioner CLI.

<br>

**Provisioner CLI:**

```bash
provisioner plugins install
```

**PyPi via pip:**

```bash
pip install provisioner-installers-plugin
```

```bash
pip install provisioner-single-board-plugin
```

```bash
pip install provisioner-examples-plugin
```