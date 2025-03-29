---
layout: docs
title: Repository Structure
description: A comprehensive guide to the Provisioner repository architecture
group: getting-started
toc: true
---

## Repository Organization

The Provisioner project follows a modular architecture designed for extensibility and maintainability. This section provides a detailed overview of the repository structure to help you navigate and contribute effectively.

### Core Components

```
provisioner/
├── provisioner/             # Runtime core package
├── provisioner_shared/      # Shared utilities and components
├── plugins/                 # Plugin ecosystem (submodule)
├── dockerfiles/             # Container definitions for testing
├── docs-site/               # Documentation website
└── scripts/                 # Development and CI/CD scripts
```

### Runtime Core (`provisioner/`)

The runtime core contains the central framework that powers the Provisioner CLI. It's responsible for:

- Plugin discovery and loading
- Command-line interface management
- Core commands implementation
- Configuration handling

### Shared Components (`provisioner_shared/`)

The shared package provides common utilities and components used by both the core runtime and plugins:

- Remote connection utilities
- Test frameworks and helpers
- Shared UI components
- Common data models and interfaces

This design ensures consistency across plugins and reduces code duplication.

### Plugin Ecosystem (`plugins/`)

Plugins extend the functionality of Provisioner with specific capabilities:

```
plugins/
├── provisioner_examples_plugin/     # Example plugin for learning
├── provisioner_single_board_plugin/ # Single-board computer management
└── provisioner_installers_plugin/   # Software installation utilities
```

Each plugin is a standalone Python package that adheres to the Provisioner plugin interface, allowing for dynamic discovery and loading at runtime.

### Development Environment

#### Poetry for Dependency Management

Provisioner uses Poetry for dependency management and packaging:

- Each component (core, shared, plugins) has its own `pyproject.toml` file
- Virtual environments are isolated for clean development
- Dependencies are precisely specified with version constraints

#### VS Code Integration

The repository includes VS Code configurations to enhance the development experience:

- Debugger configurations
- Recommended extensions
- Workspace settings optimized for Python development

#### Testing Infrastructure

The project includes comprehensive testing infrastructure:

- Unit and integration tests for all components
- End-to-end (E2E) tests using Docker containers
- Pytest as the testing framework
- Coverage reporting tools

## Development Workflow

The repository supports a streamlined development workflow:

1. **Development Mode**: Use `make dev-mode` to set up local development
2. **Testing**: Run tests with `make test` or more specific test commands
3. **Building**: Package components with Poetry
4. **Documentation**: Update and preview documentation in the `docs-site` directory

For more detailed information on the development process, see the [Development Guide](./development.md).

// TODO: Python .venv using Poetry, the shared plugin, VSCode integration etc..