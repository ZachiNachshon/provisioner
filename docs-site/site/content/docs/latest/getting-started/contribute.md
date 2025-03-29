---
layout: docs
title: Contributing to Provisioner
description: Guidelines and best practices for contributing to the Provisioner project
group: getting-started
toc: true
aliases: "/docs/latest/getting-started/contribute/"
---

## Contribution Guidelines

Provisioner is an open-source project that welcomes contributions from the community. This guide will help you understand how to contribute effectively and ensure your contributions align with the project's standards.

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Addressing issues in the existing codebase
- **Feature enhancements**: Improving existing functionality
- **Documentation**: Clarifying or expanding documentation
- **Tests**: Improving test coverage and test utilities

### Development Standards

All contributions should adhere to these standards:

#### Code Quality

- Follow PEP 8 style guidelines
- Maintain consistent code styling (use `make fmt` to format code)
- Write self-documenting code with clear naming
- Keep functions focused and modular
- Limit complexity in individual functions

#### Testing

- Maintain or increase test coverage
- Include unit tests for new functionality
- Add integration tests for component interactions
- Include E2E tests for user-facing features
- Run the full test suite before submitting a PR

#### Documentation

- Update relevant documentation for any code changes
- Document public APIs and interfaces
- Provide clear examples for new functionality

## Contribution Process

### 1. Prepare Your Environment

Before contributing, set up your development environment:

```text
# Fork this repository in GitHub

# Clone the repository
git clone https://github.com/YourUserName/provisioner.git
cd provisioner

# Initialize plugins submodule
make plugins-init

# Switch to development mode
make dev-mode

# Install dependencies
make deps-install

# Run tests to ensure everything works
make test-all-in-container
```

### 2. Create a Branch

Create a branch for your contribution:

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names that reflect your changes:

- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `test/` for test-related changes

### 3. Make Your Changes

As you develop, follow these practices:

- Make focused, logically atomic commits
- Write clear commit messages that explain the "why" not just the "what"
- Run tests frequently to catch issues early
- Format your code using `make fmt`
- Check style compliance with `make fmtcheck`

### 4. Submit a Pull Request on Forked Repository

When you're ready to submit your changes:

1. Push your branch to your fork
2. Create a pull request against the main repository
3. Fill out the pull request template thoroughly
4. Link any relevant issues

Your PR description should:

- Clearly explain what the changes are
- Describe why the changes are valuable
- Note any potential side effects or limitations

### 5. Code Review Process

After submitting a PR:

1. Automated tests will run to verify your changes
2. Maintainers will review your code
3. Address any feedback or requested changes
4. Once approved, a maintainer will merge your contribution

## Best Practices

### Keep PRs Focused

Small, focused PRs are easier to review and more likely to be merged quickly. If you're working on a large feature, consider breaking it down into smaller, logically separate PRs.

### Communication

If you're planning a significant contribution, consider:

- Opening an issue first to discuss your approach
- Engaging with the community on GitHub Discussions
- Sharing early drafts for feedback

### Dependencies

Avoid adding new dependencies unless absolutely necessary. If a new dependency is essential:

- Explain why it's needed in your PR
- Consider the license compatibility
- Evaluate maintenance status and community support

<!-- ## Creating Plugins

Plugins are a powerful way to extend Provisioner's functionality. If you're creating a new plugin:

1. Use the examples plugin as a reference
2. Follow the plugin interface specifications
3. Include comprehensive tests and documentation
4. Consider packaging and distribution requirements

For detailed guidance on plugin development, see the [Plugin Development Guide](../framework/plugins.md). -->

## Getting Help

If you need assistance while contributing:

- Check existing documentation
- Look for similar issues in the issue tracker
- Ask questions in GitHub Discussions
- Reach out to the maintainers
