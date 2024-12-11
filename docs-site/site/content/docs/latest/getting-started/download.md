---
layout: docs
title: Download
description: Download `provisioner` package / source-files to any environment, local or CI.
group: getting-started
toc: true
---

## Package Manager

Pull in `provisioner`'s package from PyPi via pip.

### PyPi

The fastest way (for `macOS` and `Linux`) to install `provisioner` is from [PyPi](https://pypi.org/) via pip:

```bash
pip install provisioner-runtime
```

<!-- ## Pre-Built Release

1. Update the download script with the following parameters:

     - **VERSION:** package released version
     - **OS_ARCH:** operating system &amp; architecture tuple

1. Download and install `provisioner` package (copy & paste into a terminal):

```bash
bash <<'EOF'

# Change Version, OS and Architecture accordingly
VERSION=0.1.0

OS_ARCH=darwin_amd64
# Options: 
#   - darwin_arm64
#   - linux_arm64
#   - linux_armv6
#   - linux_amd64

# Create a temporary folder
repo_temp_path=$(mktemp -d ${TMPDIR:-/tmp}/provisioner-repo.XXXXXX)
cwd=$(pwd)
cd ${repo_temp_path}

# Download & extract
echo -e "\nDownloading provisioner to temp directory...\n"
curl -SL "https://github.com/ZachiNachshon/provisioner/releases/download/v${VERSION}/provisioner_${VERSION}_${OS_ARCH}.tar.gz" | tar -xz

# Create a dest directory and move the binary
echo -e "\nMoving binary to ~/.local/bin"
mkdir -p ${HOME}/.local/bin; mv provisioner ${HOME}/.local/bin

# Add this line to your *rc file (zshrc, bashrc etc..) to make `provisioner` available on new sessions
echo "Exporting ~/.local/bin (make sure to have it available on PATH)"
export PATH="${PATH}:${HOME}/.local/bin"

cd ${cwd}

# Cleanup
if [[ ! -z ${repo_temp_path} && -d ${repo_temp_path} && ${repo_temp_path} == *"provisioner-repo"* ]]; then
	echo "Deleting temp directory"
	rm -rf ${repo_temp_path}
fi

echo -e "\nDone (type 'provisioner' for help)\n"

EOF
```

Alternatively, you can download a release directy from GitHub

<a href="{{< param "download.dist" >}}" class="btn btn-bd-primary" onclick="ga('send', 'event', 'Getting started', 'Download', 'Download Provisioner');" target="_blank">Download Specific Release</a>

{{< callout warning >}}
## `PATH` awareness

Make sure `${HOME}/.local/bin` exists on the `PATH` or sourced on every new shell session.
{{< /callout >}} -->

## Build from Source

Clone `provisioner` repository into a directory of your choice and run the following:

```text
$ git clone https://github.com/ZachiNachshon/provisioner.git
$ cd provisioner

# Link the provisioner-plugins sub-modules git repository
$ make plugins-init

# Update developement dependencies on all modules based on provisioner pyproject.toml
$ make dev-mode-all

# Link local provisioner module as source dependent for all other modules 
$ make use-provisioner-from-sources
```

{{< callout info >}}
{{< js.inline >}}
***Note:** Python `{{ $.Site.Params.python_version }}` is required to build from source.*
{{< /js.inline >}}
{{< /callout >}}
