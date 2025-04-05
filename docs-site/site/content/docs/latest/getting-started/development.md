---
layout: docs
title: Development
description: Set up a local development environment for both the provisioner runtime and its plugins
group: getting-started
toc: true
---

## Tooling setup

- [Python](https://www.python.org/) `v3.11` is required for packaging and tests
- [Node.js](https://nodejs.org/en/download/) is optional for managing the documentation site

{{< callout info >}}
Docs site is using npm scripts to build the documentation and compile source files. The `package.json` houses these scripts which used for various docs development actions.
{{< /callout >}}

## Quickstart Development

1. Clone the repository

   ```bash
   git clone https://github.com/ZachiNachshon/provisioner.git
   ```

1. Initialize the plugins git sub-module

   ```bash
   make plugins-init
   ```

1. Switch to **DEV** mode

   ```bash
   make dev-mode
   ```

1. Install dependencies and dev-dependencies

   ```bash
   make deps-install
   ```

1. Run tests suite

   ```bash
   make test-all-in-container
   ```

1. Run any CLI command directly from sources

   ```text
   $ make run 'config view'

   OR

   $ poetry run provisioner config view
   ```

{{< callout warning >}}
Make sure to switch back to **PROD** mode using `make prod-mode` before pushing changes to a remote branch.
{{< /callout >}}

## Development Scripts

The `makefile` within the repository root folder contains numerous tasks used for project development. Run `make` to see all the available scripts in your terminal.

{{< bs-table >}}
| Task | Description |
| --- | --- |
| `prod-mode` | Enable production mode for packaging and distribution |
| `dev-mode` | Enable local development |
| `deps-install` | Update and install pyproject.toml dependencies on all virtual environments |
| `run` | Run provisioner CLI from sources (Usage: `make run 'config view'`) |
| `fmtcheck` | Validate Python code format and imports |
| `fmt` | Format Python code using Black style and sort imports |
| `test` | Run tests suite on runtime and all plugins (output: None) |
| `test-coverage-html` | Run tests suite on runtime and all plugins (output: HTML report) |
| `test-coverage-xml` | Run tests suite on runtime and all plugins (output: XML report) |
| `pip-install-runtime` | [LOCAL] Install provisioner runtime to local pip |
| `pip-install-plugin` | [LOCAL] Install any plugin to local pip (`make pip-install-plugin example`) |
| `pip-uninstall-runtime` | [LOCAL] Uninstall provisioner from local pip |
| `pip-uninstall-plugin` | [LOCAL] Uninstall any plugins source distributions from local pip (`make pip-uninstall-plugin example`) |
| `clear-project` | Clear Poetry virtual environments and clear Python cache |
| `docs-site` | Run a local documentation site |
| `docs-site-lan` | Run a local documentation site (LAN available) |
| `plugins-init` | Initialize Provisioner Plugins git-submodule (only on fresh clone) |
| `plugins-status` | Show plugins submodule status (commit-hash) |
| `plugins-fetch` | Prompt for Provisioner Plugins commit-hash to update the sub-module |
{{< /bs-table >}}

## Testing Locally

This repository had been developed using the TDD methodology (Test Driven Development). Tests allow you to make sure your changes work as expected, don't break existing code and keeping code coverage high.

Running tests locally allows you to have short validation cycles instead of waiting for the PR status to complete.

**How to run a test suite?**

Use either `make test-all-in-container` or use the dedicated test script full command `./run_tests.py -h`.

There are two methods to export tests coverge data:

1. **Local** - run `make test-coverage-html` and click on the summary link to get into HTML formatted report
1. **CI** - run `make test-coverage-xml` and upload the XML coverage report to your favorite code cov platform

<br>

#### Running a specific test class

In order to run a specific tests class, a root relative path should be used, for example:

```text
# Running a single test class
./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/config/domain/config_test.py

# Running a specific test method
./run_tests.py provisioner_shared/components/remote/remote_connector_test.py::TestClassName::test_method_name
```

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
- Open [http://localhost:7001/](http://localhost:7001/) in your browser

Learn more about using Hugo by reading its [documentation](https://gohugo.io/documentation/).

{{< callout info >}}
Makefile contains a `make docs-site` command that does all of the above for you, it allows a quick start of the documentation site.
{{< /callout >}}

## Troubleshooting

In case you encounter problems with missing dependencies, run `make clear-project` and start over.
