#!/usr/bin/env python3

import argparse
import tomlkit

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Update dev-dependencies in pyproject.toml file.')
parser.add_argument('source', type=str, help='Path to the source pyproject.toml file')
parser.add_argument('target', type=str, help='Path to the target pyproject.toml file')
args = parser.parse_args()

# Load the source pyproject.toml file
with open(args.source, "r") as source_file:
    source_toml = tomlkit.parse(source_file.read())
    source_dev_deps = source_toml["tool"]["poetry"]["dev-dependencies"]
    source_mypy = source_toml.get("tool", {}).get("mypy", {})
    source_ruff = source_toml.get("tool", {}).get("ruff", {})
    source_black = source_toml.get("tool", {}).get("black", {})

# Load the target pyproject.toml file
with open(args.target, "r") as target_file:
    target_toml = tomlkit.parse(target_file.read())

# Ensure the dev-dependencies key exists in the target pyproject.toml file
if "dev-dependencies" not in target_toml["tool"]["poetry"]:
    target_toml["tool"]["poetry"]["dev-dependencies"] = {}

# Add the development dependencies and tool configurations to the target pyproject.toml file
target_toml["tool"]["poetry"]["dev-dependencies"].update(source_dev_deps)
target_toml["tool"]["mypy"] = source_mypy
target_toml["tool"]["ruff"] = source_ruff
target_toml["tool"]["black"] = source_black

# Write the updated target pyproject.toml file back to disk
with open(args.target, "w") as target_file:
    target_file.write(tomlkit.dumps(target_toml))
