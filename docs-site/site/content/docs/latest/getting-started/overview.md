---
layout: docs
title: Design Philosophy
description: Understanding Provisioner's architectural principles and the problems it solves
group: getting-started
toc: true
---

## The Provisioner Philosophy

Provisioner was created to solve common challenges faced by DevOps, platform, and infrastructure teams. It combines the flexibility of individual CLI tools with the consistency and safety of a unified framework. This document explains the core principles that drove Provisioner's design and the problems it solves.

## Core Principles

### Modularity and Extensibility

Provisioner's plugin architecture allows teams to build specialized tools that integrate seamlessly into a cohesive ecosystem. This approach enables:

- Independent development of domain-specific plugins
- Incremental adoption across teams and projects
- Centralized management with distributed execution

### Safety and Discoverability

Traditional scripts and utilities often lack guardrails, documentation, and standardized interfaces. Provisioner addresses these issues by:

- Enforcing consistent command patterns
- Providing built-in validation and safety checks
- Making options discoverable through interactive modes and help systems

### Flexibility and Automation

Provisioner supports both human operators and automated systems:

- Interactive mode for exploration and occasional use
- Scripted mode for integration with CI/CD and automation systems
- Environment variable support for sensitive information

## Problems Solved

### 1. Script Sprawl and Knowledge Silos

Organizations often accumulate dozens or hundreds of scripts in different languages, with varying quality and documentation. Provisioner solves this by:

- Centralizing operational tools in a consistent framework
- Making functionality self-documenting through command structure
- Reducing the "tribal knowledge" required to operate systems

### 2. Context Switching Overhead

Teams working across multiple projects and systems face cognitive overhead when switching between different tools and paradigms. Provisioner reduces this by:

- Providing a consistent interface across diverse functionality
- Standardizing option handling and error reporting
- Enabling command composition and reuse

### 3. Local-to-CI Portability

Scripts that run on a developer's workstation often behave differently in CI environments. Provisioner addresses this by:

- Supporting both interactive and non-interactive modes
- Allowing configuration through multiple channels (flags, environment variables, files)
- Providing consistent logging and error handling

### 4. Documentation-Code Synchronization

Traditional documentation quickly becomes outdated as code evolves. Provisioner mitigates this by:

- Generating help text from code
- Making options and capabilities self-documenting
- Structuring commands in intuitive hierarchies

### 5. Reliability and Safety

Ad-hoc scripts often lack error handling, validation, and safety checks. Provisioner ensures:

- Systematic validation of inputs
- Consistent error reporting
- Dry-run capabilities for sensitive operations

## Principles in Practice

To illustrate these principles, consider how Provisioner handles Raspberry Pi configuration:

**Traditional approach:**
- Multiple SSH commands
- Custom Bash scripts
- Manual edits to configuration files
- Hardcoded credentials

**Provisioner approach:**
```bash
provisioner single-board raspberry-pi node \
  --environment Remote \
  --connect-mode Flags \
  --node-username pi \
  --ip-address 192.168.1.100 \
  configure
```

This command provides:
- Interactive prompting for missing values
- Validation of inputs
- Secure credential handling
- Consistent execution workflow
- Dry-run capability

By embracing these principles, Provisioner helps teams build more maintainable, secure, and user-friendly operational tools.
