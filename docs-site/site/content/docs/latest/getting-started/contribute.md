---
layout: docs
title: Contribute
description: Contribute to the development of `provisioner` using the documentation, build scripts and tests.
group: getting-started
toc: true
aliases: "/docs/latest/getting-started/contribute/"
---

## Tooling setup

- [Python](https://www.python.org/) `v3.10` is required for packaging and tests
- [Node.js](https://nodejs.org/en/download/) is optional for managing the documentation site

{{< callout info >}}
Docs site is using npm scripts to build the documentation and compile source files. The `package.json` houses these scripts which used for various docs development actions.
{{< /callout >}}

## Guidelines

- PRs need to have a clear description of the problem they are solving
- PRs should be small
- Code without tests is not accepted, PRs must not reduce tests coverage
- Contributions must not add additional dependencies
- Before creating a PR, make sure your code is well formatted, abstractions are named properly and design is simple
- In case your contribution can't comply with any of the above please start a GitHub issue for discussion

## How to Contribute?

1. Fork this repository
1. Create a PR on the forked repository
1. Send a pull request to the upstream repository

## Development Scripts

The `makefile` within this repository contains numerous tasks used for project development. Run `make` to see all the available scripts in your terminal.

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `dev-mode-all` | Update dev dependencies and their config based on provisioner pyproject.toml |
| `update-externals-all` | Update external source dependents |
| `deps-all` | Update and install pyproject.toml dependencies on all virtual environments |
| `fmtcheck-all` | Validate Python code format and imports |
| `fmt-all` | Format Python code using Black style and sort imports |
| `test-all` | Run Unit/E2E/IT tests suite |
| `test-coverage-xml-all` | Run Unit/E2E/IT tests with coverage reports |
| `use-provisioner-from-sources` | Use provisioner as a direct sources dependency to all Python modules (for testing in CI) |
| `use-provisioner-from-pypi` | Use provisioner as a PyPi package to all Python modules (for testing in CI) |
| `pip-install` | Install provisioner sdist to local pip |
| `pip-install-plugins` | Install all plugins source distributions to local pip |
| `pip-uninstall` | Uninstall provisioner from local pip |
| `pip-uninstall-plugins` | Uninstall all plugins source distributions from local pip |
| `clear-virtual-env-all` | Clear all Poetry virtual environments |
| `docs-site` | Run a local documentation site |
| `docs-site-lan` | Run a local documentation site (LAN available) |
| `pDev` | Interact with `./external/.../poetry_dev.sh` (Usage: `make pDev 'fmt --check-only'`) |
| `pReleaser` | Interact with `./external/.../poetry_pip_releaser.sh` (Usage: `make pReleaser 'install --build-type sdist --multi-project'`) |
| `plugins-init` | Initialize Provisioner Plugins git-submodule (only on fresh clone) |
| `plugins-status` | Show plugins submodule status (commit-hash) |
| `plugins-fetch` | Prompt for Provisioner Plugins commit-hash to update the sub-module |
{{< /bs-table >}}

## Testing Locally

This repository had been developed using the TDD methodology (Test Driven Development). Tests allow you to make sure your changes work as expected, don't break existing code and keeping code coverage high.

Running tests locally allows you to have short validation cycles instead of waiting for the PR status to complete.

**How to run a test suite?**

1. Clone the `provisioner` repository
2. Run `make tests-all` to use the locally installed Python interpreter
3. Alternatively, run `make test-coverage-xml-all` if you are interested in coverage reports

## Documentation Scripts

The `/docs-site/package.json` includes numerous tasks for developing the documentation site. Run `npm run` to see all the available npm scripts in your terminal. Primary tasks include:

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `npm run docs-build` | Cleans the Hugo destination directory for a fresh serve |
| `npm run docs-serve` | Builds and runs the documentation locally |
{{< /bs-table >}}

## Local documentation 

Running the documentation locally requires the use of Hugo, which gets installed via the `hugo-bin` npm package. Hugo is a blazingly fast and quite extensible static site generator. Here’s how to get it started:

- Run through the [tooling setup](#tooling-setup) above to install all dependencies
- Navigate to `/docs-site` directory and run `npm install` to install local dependencies listed in `package.json`
- From `/docs-site` directory, run `npm run docs-serve` in the command line
- Open [http://localhost:9001/](http://localhost:9001/) in your browser

Learn more about using Hugo by reading its [documentation](https://gohugo.io/documentation/).

{{< callout info >}}
Makefile contains a `make docs-site` command that does all of the above for you, it allows a quick start of the documentation site.
{{< /callout >}}

## Troubleshooting

In case you encounter problems with missing dependencies, run `make clear-virtual-env-all` and start over.
