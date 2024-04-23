---
layout: docs
title: Overview
description: Learn about <code>provisioner</code>, why it was created and the pain it comes to solve.
group: getting-started
toc: true
---

## Why creating `provisioner`?

1. Allow a better experience for teams using multiple sources of managed scripts, make them approachable and safe to use by having a tested, documented and controlled process with minimum context switches, increasing engineers velocity

1. Allowing to compose different actions from multiple channels (shell scripts, CLI utilities, repetitive commands etc..) into a coherent well documented plugin

1. Having the ability to run the same action from CI on a local machine and vice-versa. Execution is controlled with flavored flags or differnet configuration set per environment

1. Remove the fear of running an arbitrary undocumeted script that relies on ENV vars to control its execution

1. Use only the plugins that you care about, search the plugins marketplace and install (or pre-install) based on needs

1. Reduce the amount of CLI utilities created in a variety of languages in an organization

1. Interaction with `provisioner` support both user experience:
   - Interactive TUI (terminal GUI) enriched with step-by-step documentation and guidance
   - Non-interactive mode i.e. direct CLI command
   