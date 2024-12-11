#!/usr/bin/env python3
import argparse
import os

# Base development and production lines to toggle
development_template = "provisioner-shared = { path = \"{repo_path}/provisioner_shared\", develop = true }"
production_line_prefix = "provisioner-shared = \"^"

def resolve_repo_path():
    """Resolve the absolute path of the repository."""
    current_dir = os.path.abspath(os.getcwd())
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, ".git")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise RuntimeError("Repository root not found.")

def update_pyproject_toml(pyproject_path, mode):
    """Switch between development and production mode in pyproject.toml."""
    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} does not exist.")
        return

    with open(pyproject_path, "r") as file:
        content = file.read()

    repo_path = resolve_repo_path()
    development_line = development_template.format(repo_path=repo_path)

    if mode == "dev":
        if development_line in content:
            print(f"{pyproject_path} is already in development mode.")
        else:
            content = replace_line(content, production_line_prefix, development_line)
            with open(pyproject_path, "w") as file:
                file.write(content)
            print(f"Switched {pyproject_path} to development mode.")

    elif mode == "prod":
        if any(line.startswith(production_line_prefix) for line in content.splitlines()):
            print(f"{pyproject_path} is already in production mode.")
        else:
            content = replace_line(content, development_line, production_line_prefix + "<version>\"")
            with open(pyproject_path, "w") as file:
                file.write(content)
            print(f"Switched {pyproject_path} to production mode. Update the version as needed.")

    else:
        print("Invalid mode. Use 'dev' or 'prod'.")

def replace_line(content, old_line_start, new_line):
    """Replace a line in the content based on its start string."""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(old_line_start):
            lines[i] = new_line
            break
    return "\n".join(lines)

def process_plugins(mode):
    """Iterate through plugins and update their pyproject.toml files."""
    repo_path = resolve_repo_path()
    plugins_path = os.path.join(repo_path, "plugins")

    if not os.path.exists(plugins_path):
        print(f"Error: Plugins directory '{plugins_path}' does not exist.")
        return

    for folder in os.listdir(plugins_path):
        folder_path = os.path.join(plugins_path, folder)
        if os.path.isdir(folder_path) and folder.endswith("_plugin"):
            pyproject_path = os.path.join(folder_path, "pyproject.toml")
            update_pyproject_toml(pyproject_path, mode)

def main():
    parser = argparse.ArgumentParser(description="Switch between development and production modes in pyproject.toml for plugins.")
    parser.add_argument("mode", choices=["dev", "prod"], help="Mode to switch to: 'dev' or 'prod'.")
    args = parser.parse_args()

    process_plugins(args.mode)

if __name__ == "__main__":
    main()
