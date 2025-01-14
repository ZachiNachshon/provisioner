---
layout: docs
title: Configuration
description: Manage custom user configuration or use defaults
group: content
toc: true
aliases: "/docs/latest/configuration/"
---

## Usage

Provisioner and plugins are using internal configurations with an option for users to override any config value. Run `provisioner config` to get a list of available config management commands.

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `clear` | Clear local config file to rely only on managed configuration |
| `edit` | Edit configuration file |
| `flush` | Flush configuration defaults to a file (path: `~/.config/provisioner/config.yaml`) |
| `view` | Print configuration to stdout |
{{< /bs-table >}}

<br>

#### Internal Configuration

By default, `provisioner` and its plugins use internal configurations with default values.
These internal configurations are located in each module's source files under the path `<module-name>/resources/config.yaml`. They are embedded into the package during the release process.

```text
├── ...
├── provisioner
│   └── resources
│       ├── config.yaml
│       └── ...       
├── plugins                   
│   ├── provisioner-installers-plugin
│   │    └── provisioner-installers-plugin
│   │        ├── resources
│   │        │   ├── config.yaml
│   │        │   └── ...
│   │        ├── poetry.toml
│   │        ├── pyproject.toml
│   │        └── ...
│   ├── additional modules
│   └── ...  
```

<br>

#### User Configuration

Internal configuration values in a released package are immutable and serve as default settings. To override these default values (user-specific configuration), you can create a custom configuration file at `~/.config/provisioner/config.yaml`, specifying the desired configuration hierarchy to be overridden.

To view the configuration schema for the provisioner runtime and any installed plugins, use the command:
`provisioner config view`

{{< callout info >}}
Run `provisioner config flush` to create a `config.yaml` file and flushing internal configuration into it to act as a baseline of what can be overridden.
{{< /callout >}}
