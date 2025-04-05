---
layout: docs
title: How Provisioner Bootstraps
description: Understanding the entry point, configuration loading, and plugin system
group: bootstrap
toc: true
---

## Entry Point Architecture

Provisioner follows a modular architecture with a lightweight core that dynamically discovers and loads plugins. This document provides a high-level overview of how the system bootstraps.

### Main Entry Point

The CLI bootstrap process begins in `main.py`, which serves as the entry point for the entire application. When you run the `provisioner` command, the following sequence occurs:

```
┌─ Provisioner CLI ─────────────────────────┐
│                                           │
│  1. Process pre-run arguments             │
│  2. Initialize core collaborators         │
│  3. Create CLI command structure          │
│  4. Load configuration                    │
│  5. Register core commands                │
│  6. Discover and load plugins             │
│  7. Execute requested command             │
│                                           │
└───────────────────────────────────────────┘
```

## Configuration Management

Provisioner loads configuration from two primary sources:

1. **Internal Configuration**: Built-in defaults located at `resources/config.yaml` within the package
2. **User Configuration**: User-specific settings in the home directory at `~/.provisioner/config.yaml`

The configuration system prioritizes user settings, allowing you to override default values while maintaining a consistent base configuration.

```python
# Configuration loading from main.py
ConfigManager.instance().load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig)
```

## Plugin System

Provisioner's functionality is primarily delivered through plugins. The core is responsible for discovering, loading, and integrating these plugins into the CLI.

### Plugin Discovery

The CLI scans installed Python packages that match the "provisioner" naming pattern, excluding core packages:

```python
cols.package_loader().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner-runtime", "provisioner_runtime", "provisioner_shared", "provisioner-shared"],
    callback=lambda module: load_plugin(plugin_module=module),
)
```

This means any Python package installed via pip with a name containing "provisioner" and conforming to the plugin interface will be automatically discovered and loaded.

### Plugin Integration

Each plugin must implement two key functions to integrate with the core:

1. **`load_config()`**: Loads plugin-specific configuration
2. **`append_to_cli(root_menu)`**: Registers plugin commands with the CLI

```python
def load_plugin(plugin_module):
    plugin_module.load_config()
    plugin_module.append_to_cli(root_menu)
```

## Plugin vs. Core Structure

Understanding the difference between core and plugin components:

| Aspect | Core (Runtime) | Plugins |
|--------|---------------|---------|
| Purpose | Provides framework, discovery, and infrastructure | Implements domain-specific functionality |
| Location | `provisioner` package | External packages (`provisioner_*_plugin`) |
| Entry point | `main.py` at runtime root | `main.py` in each plugin package |
| Configuration | Loads global config | Loads plugin-specific config |
| Commands | Core utilities (version, config, plugins) | Domain-specific commands |

## Next Steps

Now that you understand how Provisioner bootstraps, proceed to:

- [Create a New Plugin](create-a-new-plugin.md) to extend Provisioner with your own functionality
- [Plugin Architecture](../framework/plugins.md) for detailed plugin design
- [Command Development](../framework/command-system.md) to learn how commands work
- [Configuration System](../framework/configuration.md) for advanced configuration options 