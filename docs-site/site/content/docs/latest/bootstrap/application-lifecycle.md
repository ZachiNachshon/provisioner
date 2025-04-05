---
layout: docs
title: High-Level Application Lifecycle
description: Understanding the flow of a provisioner & plugins application lifecycle
group: bootstrap
toc: true
---

## Application Lifecycle Overview

The Provisioner application follows a well-defined lifecycle from the moment you execute the CLI command until your requested action is performed. Understanding this flow helps you troubleshoot issues and develop plugins that integrate seamlessly with the framework.

## Startup Sequence

When you run a Provisioner command, the application follows this sequence:

### 1. Command Invocation

The process begins when you execute the `provisioner` command with arguments:

```bash
provisioner [global-flags] [command] [command-args]
```

### 2. Core Initialization

The application initializes the core infrastructure:

- Creates an empty context object
- Sets up core collaborators (logging, package loading, etc.)
- Establishes the root CLI menu structure

### 3. Configuration Loading

Configuration is loaded from two sources:

- **Internal configuration**: Default settings packaged with Provisioner (`resources/config.yaml`)
- **User configuration**: Custom settings in the user's home directory (`~/.provisioner/config.yaml`)

User settings override internal defaults, allowing for customization while maintaining required base configuration.

### 4. Core Command Registration

The application registers built-in commands:

- `version`: Shows version information
- `config`: Manages configuration settings
- `plugins`: Lists and manages installed plugins

### 5. Plugin Discovery and Loading

Provisioner dynamically discovers and loads plugins:

1. Scans installed Python packages matching the "provisioner" pattern
2. For each plugin:
   - Loads plugin-specific configuration
   - Registers plugin commands with the CLI

### 6. Command Execution

Finally, the application:

1. Processes arguments to identify the requested command
2. Sets up the execution context with relevant flags
3. Executes the command's implementation
4. Returns the result and exit code

## Application Lifecycle Flowchart

```
┌─────────────────────────────┐
│    User Invokes Command     │
│ provisioner [cmd] [args]    │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│    Initialize Core System   │
│    Create Empty Context     │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│    Create CLI Structure     │
│    Set Up Command Backbone  │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│  Load Configuration         │◄────┐
│  Internal + User Config     │     │
└───────────────┬─────────────┘     │
                ▼                   │
┌─────────────────────────────┐     │
│  Register Core Commands     │     │
│  version, config, plugins   │     │
└───────────────┬─────────────┘     │
                ▼                   │
┌─────────────────────────────┐     │
│    Discover Pip Packages    │     │
│    Filter "provisioner*"    │     │
└───────────────┬─────────────┘     │
                ▼                   │
┌─────────────────────────────┐     │
│       For Each Plugin       │     │
└───────────────┬─────────────┘     │
                ▼                   │
┌─────────────────────────────┐     │
│    Load Plugin Config       ├─────┘
│                             │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│  Register Plugin Commands   │
│      with CLI Menu          │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│   Process User Command      │
│   Validate Arguments        │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│      Execute Command        │
│                             │
└───────────────┬─────────────┘
                ▼
┌─────────────────────────────┐
│     Return Result/Exit      │
│                             │
└─────────────────────────────┘
```

## Key Components in the Lifecycle

### Configuration Manager

The `ConfigManager` is a singleton that:
- Loads internal and user configuration
- Validates configuration against schema
- Provides access to config values
- Manages plugin-specific configuration

### CLI Modifiers

CLI modifiers affect how commands are executed:
- `--dry-run (-d)` : Simulates command execution without making changes
- `--verbose (-v)` : Enables verbose logging

### Plugin Integration Points

Plugins integrate at specific points in the lifecycle:
1. During discovery, when the package loader finds them
2. During configuration loading, when plugin-specific settings are loaded
3. During CLI registration, when plugin commands are added to the menu
4. During command execution, when plugin-provided commands are invoked

## Customization Points

The Provisioner lifecycle can be customized at several points:

1. **User Configuration**: Override default settings in `~/.provisioner/config.yaml`
2. **Command-Line Flags**: Modify behavior with global flags
3. **Environment Variables**: Configure certain aspects via environment
4. **Plugin Loading**: Control which plugins are loaded and their order
5. **Command Implementation**: Plugins can implement custom commands with unique behavior

## Next Steps

Now that you understand the application lifecycle, you can:

- [Create a New Plugin](create-a-new-plugin.md) to extend Provisioner
- Learn about [Plugin Development](../framework/plugins.md) in depth
- Explore the [Configuration System](../framework/configuration.md) 