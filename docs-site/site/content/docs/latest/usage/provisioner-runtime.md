---
layout: docs
title: Provisioner Runtime
description: Python powered CLI for dynamic plugin management.
group: usage
toc: true
aliases: "/docs/latest/usage/"
---

## Runtime Engine

The `provisioner-runtime` pip package is required to dynamically load any plugin it finds installed as pip packages.

Provisioner plugins are configured to hook into provisioner CLI menu and add its commands so they'll become visibile once those are identified by provisioner at runtime.

Removing such plugins from pip will remove them from `provisioner` CLI menu as well.

## Framework

Provisioner is used as a framework for creating new plugins in a no-brainer manner, simple and quick.

Is is a fully featured Python CLI framework supports a wide range of common utilities, interactive terminal and core capabilities such as config-management, flag modifiers (verbose, dry-run, auto-prompt) and much more...

Partial list of available features:

* Configuration management (internal and custom user config)
* Collaborators utilities ([lightweight wrappers for common actions](https://github.com/ZachiNachshon/provisioner/blob/05d11dbadd18ac98f44b4b95f8b34e4dd2f00c90/provisioner/provisioner/shared/collaborators.py#L24))
* Ansible programmatic wrapper for running as-hoc commands or Ansible playbooks - simply and easily 
* Flags modifiers out of the box (verbose, silent, dry-run, auto-prompt, non-interactive)
* CLI application lifecycle made easy, simply structured and extensible
* (Optional) [Functional library](https://github.com/ZachiNachshon/provisioner/blob/master/provisioner/provisioner/func/pyfn.py#L27) for writing functional plugins ([see installers plugin for example](https://github.com/ZachiNachshon/provisioner-plugins/blob/master/provisioner_installers_plugin/provisioner_installers_plugin/installer/runner/installer_runner.py#L131))
* [Remote connector](https://github.com/ZachiNachshon/provisioner/blob/master/provisioner_features_lib/provisioner_features_lib/remote/remote_connector.py#L48) that encapsulates all remote SSH info collection from different sources (config, user, flags, env vars), acts as a single connection point to any remote machine
* And much more...

<br>

#### Poetry

To use `provisioner-runtime` as a Python package using the Poetry package manager, add the following to the `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
python = "^3.10"
provisioner-runtime = "^0.1.10"
```

