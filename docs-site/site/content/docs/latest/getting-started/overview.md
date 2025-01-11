---
layout: docs
title: Overview
description: Discover the purpose of <code>provisioner</code>, the challenges it was designed to solve, and the solutions it provides
group: getting-started
toc: false
---

## Why creating `provisioner`?

1. Enhance the experience for teams using multiple sources of managed scripts. Make them approachable and safe by providing a tested, documented, and controlled process with minimal context switching, thereby increasing engineering velocity

1. Enable the composition of various actions from multiple sources (e.g., shell scripts, CLI utilities, repetitive commands) into a coherent and well-documented plugin

1. Facilitate running the same actions both locally and in CI environments. Execution is managed through flexible flags or different configuration sets for each environment

1. Eliminate the risks associated with running arbitrary, undocumented scripts that rely on environment variables for execution

1. Allow teams to use only the plugins they need by searching the plugins marketplace and installing (or pre-installing) them as required

1. Reduce the proliferation of CLI utilities written in various languages within an organization

1. Provide a dual user experience when interacting with `provisioner`:
   - Interactive Mode: A terminal-based UI (TUI) enriched with step-by-step documentation and guidance
   - Non-Interactive Mode: Direct execution through CLI commands
