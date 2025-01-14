---
layout: docs
title: Provisioner Runtime
description: Python powered CLI for dynamic plugins management.
group: plugins
toc: true
aliases: "/docs/latest/plugins/"
---

## Runtime Engine

The `provisioner-runtime` pip package is required to dynamically load plugins from the local pip environment.

Provisioner plugins are designed to integrate with the provisioner CLI menu. Their commands become visible once the plugins are identified and loaded by provisioner at runtime.

Uninstalling such plugins from pip will automatically remove their commands from the `provisioner` CLI menu.

### Plugins

Provisioner includes a built-in `plugins` CLI command for managing plugins. To view a list of available commands:

```bash
provisioner plugins
```

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `install` | Search and install plugins from remote |
| `list` | List locally installed provisioner plugins |
| `uninstall` | Select local plugins to uninstall |
{{< /bs-table >}}


#### Poetry

This section is relevant when using the [Poetry](https://python-poetry.org/) package manager to manage Python modules. To use `provisioner-runtime` as a Python dependency simply add it to the `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
python = "^3.11"
provisioner-runtime = "^0.1.15"
```

