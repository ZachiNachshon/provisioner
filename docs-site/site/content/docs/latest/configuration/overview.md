---
layout: docs
title: Configuration
description: Manage custom user configuration or use defaults
group: content
toc: true
aliases: "/docs/latest/configuration/"
---

## Usage

Provisioner and plugins are using internal configurations with an option to override any config value.

<br>

#### Internal Configuration

By default, `provisioner` and its plugins are using internal configuration with defualt values.<br>
Internal configurations can be found on every module source files under at path `<module-name>/resources/config.yaml`, those are being baked into the package upon release.

```text
├── ...
├── provisioner
│   └── resources
│       ├── config.yaml
│       └── ...       
├── plugins                   
│   └── provisioner-installers-plugin
│       └── resources
│           ├── config.yaml
│           └── ...       
│   ├── additional modules
│   └── ...  
```

<br>

#### User Configuration

Internal config values cannot be changed on a released package, they are aimed to allow default values. When in need to override a default configuration a.k.a user-configuration, a custom config file should be created at `~/.config/provisioner/config.yaml` with the config hierarchy that is expected to get overridden.

To get the configuraton schema of either provisioner and/or the installed plugins, use `provisioner config view`.

{{< callout info >}}
Run `provisioner config flush` to create a `config.yaml` file and flushing internal configuration into it to act as a baseline of what can be overridden.
{{< /callout >}}

Provisioner allows config management via CLI commands. To get a list of available config commands, run `provisioner config`.

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `clear` | Clear local config file to rely only on managed configuration |
| `edit` | Edit configuration file |
| `flush` | Flush configuration defaults to a file (path: `~/.config/provisioner/config.yaml`) |
| `view` | Print configuration to stdout |
{{< /bs-table >}}
