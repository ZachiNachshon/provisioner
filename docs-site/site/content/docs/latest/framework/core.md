---
layout: docs
title: Core components
description: Core components declared within the provisioner framework
group: content
toc: false
---

## Framework

Provisioner is used as a framework for creating new plugins in a no-brainer manner, simple and quick.

It is a fully featured Python CLI framework supports a wide range of common utilities, interactive terminal and core capabilities such as config-management, flag modifiers (verbose, dry-run, auto-prompt) and much more...

Partial List of Available Features:

* Configuration management (internal and custom user configurations)
* Collaborator utilities ([lightweight wrappers for common actions](https://github.com/ZachiNachshon/provisioner/blob/master/provisioner_shared/components/runtime/shared/collaborators.py))
* Programmatic Ansible wrapper for running ad-hoc commands or Ansible playbooks—simple and easy to use
* Built-in flag modifiers, including verbose, silent, dry-run, auto-prompt, and non-interactive modes
* Simplified CLI application lifecycle—structured, extensible, and easy to manage
* (Optional) [Functional library](https://github.com/ZachiNachshon/provisioner/blob/master/provisioner_shared/framework/functional/pyfn.py) for creating functional plugins (e.g., the [installers plugin](https://github.com/ZachiNachshon/provisioner-plugins/blob/master/provisioner_installers_plugin/provisioner_installers_plugin/src/installer/runner/installer_runner.py))
* [Remote connector](https://github.com/ZachiNachshon/provisioner/blob/master/provisioner_shared/components/remote/remote_connector.py#L48) that encapsulates all remote SSH information collection from various sources (e.g., config, user inputs, flags, and environment variables), providing a single connection point to any remote machine
* And much more...

<br>

**Table of contents**

* [Environment](#environment)
* [Context](#context)
* [Serialization](#serialization)
* [Time](#time)
* [General Utilities](#utilities)
* [Errors](#errors)
