<h3 align="center" id="provisioner-logo"><img src="assets/provisioner-single.svg" height="300"></h3>

<p align="center">
  <a href="#requirements">Requirements</a> •
  <a href="#quickstart">QuickStart</a> •
  <a href="#overview">Overview</a> •
  <a href="#contribute">Contribute</a> •
  <a href="#support">Support</a> •
  <a href="#license">License</a>
</p>
<br>

**Provisioner** is a CLI utility and a Python based framework for creating and loading dynamic plugins extensions. 

It is dynamic because it detects installed plugins as pip packages and dynamically load their declared commands into Provisioner's CLI main menu.

It comes with built-in CLI capabilities, such as:
* Flag modifiers (verbose, dry-run, auto-prompt)
* Self update 
* Config management 
* Auto completions
* Version command

| :heavy_exclamation_mark: WARNING |
| :--------------------------------------- |
| Provisioner is still in **alpha stage**, breaking changes might occur. |

<br>

<h2 id="requirements">🏴‍☠️ Requirements</h2>

- A Unix-like operating system: macOS, Linux
- Python `v3.10` and above

<br>

<h2 id="quickstart">⚡️ QuickStart</h2>

The fastest way (for macOS and Linux) to install anchor is using Homebrew:

```bash
brew install ZachiNachshon/tap/provisioner
```

Alternatively, tap into the formula to have brew search capabilities on that tap formulas:

```bash
# Tap
brew tap ZachiNachshon/tap

# Install
brew install provisioner
```

For additional installation methods read here.

<br>

<h2 id="overview">⚓️ Overview</h2>

- [Why creating `Provisioner`?](#why-creating-provisioner)
- [Documentation](#documentation)
- [Playground](#playground)

**Maintainers / Contributors:**

- [Contribute guides](https://add.contribute.guide.com)

<br>

<h3 id="why-creating-provisioner">⛵ Why Creating <code>Provisioner</code>?</h3>

1. Allow a better experience for teams using multiple sources of managed scripts, make them approachable and safe to use by having a tested, documented and controlled process with minimum context switches, increasing engineers velocity

1. Allowing to compose different actions from multiple channels (shell scripts, CLI utilities, repetitive commands etc..) into a coherent well documented plugin

1. Having the ability to run the same action from CI on a local machine and vice-versa. Execution is controlled with flavored flags or differnet configuration set per environment

1. Remove the fear of running an arbitrary undocumeted script that relies on ENV vars to control its execution

1. Use only the plugins that you care about, search the plugins marketplace and install (or pre-install) based on needs

1. Reduce the amount of CLI utilities created in a variety of languages in an organization

<br>

<h3 id="documentation">📖 Documentation</h3>

Please refer to the [documentation](http://to.be.continued.com) for detailed explanation on how to configure and use `provisioner`.


<br>

<h3 id="playground">🐳 Playground</h3>

Using `provisioner`, **every** command is a playground.

Use the `--dry-run` (short: `-d`) to check command exeuction breakdown, you can also add the `--verbose` (short: `-v`) flag to read `DEBUG` information. 

*All dry-run actions are no-op, you can safely run them as they only print to stdout.*

<br>

<h2 id="contribute">Contribute</h2>

Please follow our contribution guidelines if you with to contribute:

* PRs need to have a clear description of the problem they are solving
* PRs should be small
* Code without tests is not accepted, code coverage should keep the same level or higher
* Contributions must not add additional dependencies
* Before creating a PR, make sure your code is well formatted, abstractions are named properly and design is simple
* In case your contribution can't comply with any of the above please start a github issue for discussion

<br>

<h2 id="support">Support</h2>

Provisioner is an open source project that is currently self maintained in addition to my day job, you are welcome to show your appreciation by sending me cups of coffee using the the following link as it is a known fact that it is the fuel that drives software engineering ☕

<a href="https://www.buymeacoffee.com/ZachiNachshon" target="_blank"><img src="docs-site/site/static/docs/latest/assets/img/bmc-orig.svg" height="57" width="200" alt="Buy Me A Coffee"></a>

<br>

<h2 id="license">License</h2>

MIT

<br>

---
Document for later (contribution):

To build a Python sdist with relative paths - 

Install a plugin that allow buidling sdist for a multiproject (monorepo)
See:
  - https://github.com/DavidVujic/poetry-multiproject-plugin
  - https://github.com/python-poetry/poetry/issues/5621
  - https://github.com/python-poetry/poetry-core/pull/273

```bash
poetry self add poetry-multiproject-plugin

OR

pip install poetry-multiproject-plugin
```