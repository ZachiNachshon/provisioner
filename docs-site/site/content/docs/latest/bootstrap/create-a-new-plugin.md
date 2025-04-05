---
layout: docs
title: Create a New Provisioner Plugin
description: Step-by-step guide to developing a custom plugin for the Provisioner framework
group: bootstrap
toc: true
---

## Introduction to Plugin Development

Provisioner's plugin architecture allows you to extend the framework with custom functionality while leveraging the core infrastructure. This guide will walk you through creating a new plugin from scratch.

## Plugin Structure Overview

A Provisioner plugin is a Python package that follows these conventions:

- Package name starts with `provisioner_` and ends with `_plugin`
- Contains a `main.py` file that implements the plugin interface
- Includes a `resources/config.yaml` file for plugin-specific configuration
- Structured to register commands with the CLI

## Step-by-Step Plugin Creation

### 1. Set Up the Package Structure

Start by creating the basic file structure for your plugin:

```text
mkdir -p provisioner_myplugin_plugin/provisioner_myplugin_plugin/resources
mkdir -p provisioner_myplugin_plugin/provisioner_myplugin_plugin/src
touch provisioner_myplugin_plugin/pyproject.toml
touch provisioner_myplugin_plugin/provisioner_myplugin_plugin/main.py
touch provisioner_myplugin_plugin/provisioner_myplugin_plugin/resources/config.yaml
```

### 2. Define Package Metadata

Create a `pyproject.toml` file with your plugin's metadata:

```toml
[tool.poetry]
name = "provisioner-myplugin-plugin"
version = "0.1.0"
description = "My custom plugin for Provisioner"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "provisioner_myplugin_plugin"}]

[tool.poetry.dependencies]
python = "^3.8"
provisioner-shared = "^0.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 3. Implement the Plugin Interface

Edit your `main.py` file to implement the required plugin interface:

```python
#!/usr/bin/env python3
import pathlib

import click

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.version import append_version_cmd_to_cli
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

# Define plugin constants
PLUGIN_NAME = "myplugin"
MYPLUGIN_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{MYPLUGIN_ROOT_PATH}/resources/config.yaml"

# Create config class for your plugin
from dataclasses import dataclass
from provisioner_shared.components.runtime.config.domain.config import BaseConfig

@dataclass
class MyPluginConfig(BaseConfig):
    some_setting: str = None
    enabled: bool = True

# Required function to load plugin configuration
def load_config():
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=MyPluginConfig)

# Required function to register plugin commands with the CLI
def append_to_cli(root_menu: click.Group):
    # Get plugin config
    myplugin_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    
    # Create a top-level command group for your plugin
    @root_menu.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def myplugin(ctx):
        """My custom functionality for Provisioner"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())
    
    # Add version command to your plugin's command group
    append_version_cmd_to_cli(
        root_menu=myplugin,
        root_package=MYPLUGIN_ROOT_PATH,
        description="Print myplugin version"
    )
    
    # Register your plugin's commands
    # register_my_commands(cli_group=myplugin, myplugin_cfg=myplugin_cfg)
```

### 4. Create Configuration File

Set up your plugin's configuration in `resources/config.yaml`:

```yaml
enabled: true
some_setting: "default value"
```

### 5. Implement Command Registration

Create a new file to register your plugin's commands. For example, create `src/commands.py`:

```python
import click
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers

def register_my_commands(cli_group, myplugin_cfg):
    @cli_group.command()
    @cli_modifiers
    @click.pass_context
    def hello(ctx):
        """Print a hello message"""
        click.echo("Hello from my custom plugin!")
```

Then modify your `main.py` to import and use this function:

```python
from provisioner_myplugin_plugin.src.commands import register_my_commands

# In your append_to_cli function:
register_my_commands(cli_group=myplugin, myplugin_cfg=myplugin_cfg)
```

### 6. Build and Install Your Plugin

Build your plugin package:

```bash
make pip-install-plugin myplugin
```

This will install the plugin to local pip, used for development or testing.


## Plugin Development Best Practices

### Command Organization

Organize your commands logically:

- Group related commands under meaningful subcommands
- Use consistent naming conventions for commands
- Follow the pattern used in existing plugins

### Error Handling

Implement robust error handling:

- Validate user input and configuration
- Provide meaningful error messages
- Return appropriate exit codes

### Testing

Write comprehensive tests for your plugin:

- Unit tests for individual components
- Integration tests for command execution
- Test both successful and error cases

## Examples from Existing Plugins

Study these patterns from existing plugins:

### Configuration Validation

```python
def append_to_cli(root_menu: click.Group):
    plugin_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if plugin_cfg.required_setting is None:
        raise Exception("Required setting is missing from plugin configuration")
```

## Next Steps

After creating your plugin:

- Test it thoroughly with different inputs and scenarios
- Document your plugin's functionality and configuration
- Consider publishing it to PyPI for wider usage

For more detailed information, refer to the [Plugin Architecture Guide](../framework/plugins.md). 