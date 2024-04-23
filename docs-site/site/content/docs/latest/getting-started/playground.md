---
layout: docs
title: Playground
description: Take <code>provisioner</code> for a spin by using the examples plugin.
group: getting-started
toc: true
---

## Instructions
Follow these steps to install the examples plugin and run **no-op** commands just to get the feel of using provisioner, its plugins and overall uesr experience.

1. Install the playground

   ```bash
   pip install provisioner-examples-plugin
   ```

1. List the available Ansible example commands

   ```bash
   provisioner examples ansible
   ```

1. Run an example Ansible no-op local command

   ```bash
   provisioner examples ansible hello
   ```

<br>

{{< callout info >}}
This is a quick overview just to get a grasp of how simple it is to use `provisioner`.<br>For more information, please see the [usage section](/docs/{{< param docs_version >}}/usage/structure).
{{< /callout >}}
