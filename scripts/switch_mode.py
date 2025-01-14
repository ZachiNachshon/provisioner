#!/usr/bin/env python3
import argparse
import os
import re

import tomlkit


def resolve_repo_path():
    """Resolve the absolute path of the repository."""
    current_dir = os.path.abspath(os.getcwd())
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, ".git")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise RuntimeError("Repository root not found.")


def update_root_pyproject_toml(pyproject_path, mode):
    """Switch between development and production mode in pyproject.toml."""
    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} does not exist.")
        return

    with open(pyproject_path, "r") as file:
        toml_content = tomlkit.parse(file.read())

    repo_path = resolve_repo_path()
    project_name = os.path.basename(os.path.dirname(pyproject_path))

    dependencies = toml_content["tool"]["poetry"]["dependencies"]
    prod_dependency_key = "provisioner-shared"

    plugins_path = os.path.join(repo_path, "plugins")
    if not os.path.exists(plugins_path):
        print(f"Error: Plugins directory '{plugins_path}' does not exist.")

    if mode == "dev":
        if prod_dependency_key in dependencies:
            print(f"{project_name} is already in dev mode.")
        else:
            # Add the development dependency as an inline table
            dev_dependency = tomlkit.inline_table()
            dev_dependency["path"] = f"{repo_path}/provisioner_shared"
            dev_dependency["develop"] = True
            dependencies[prod_dependency_key] = dev_dependency
            print(f"Switched {project_name} to development mode.")

        # Add or update all plugins as development dependencies
        for plugin_folder in os.listdir(plugins_path):
            plugin_path = os.path.join(plugins_path, plugin_folder)
            if os.path.isdir(plugin_path) and plugin_folder.endswith("_plugin"):
                plugin_key = plugin_folder.replace("-", "_")
                dev_dependency = tomlkit.inline_table()
                dev_dependency["path"] = plugin_path
                dev_dependency["develop"] = True
                dependencies[plugin_key] = dev_dependency
                print(f"  Added or updated plugin {plugin_key} in development mode.")

    elif mode == "prod":
        if prod_dependency_key in dependencies:
            # Remove the development dependency
            del dependencies[prod_dependency_key]
            print(f"Switched {project_name} to production mode.")
        else:
            print(f"{project_name} is already in prod mode.")

        # Remove all plugin dependencies
        for plugin_folder in os.listdir(plugins_path):
            plugin_path = os.path.join(plugins_path, plugin_folder)
            if os.path.isdir(plugin_path) and plugin_folder.endswith("_plugin"):
                plugin_key = plugin_folder.replace("-", "_")
                if plugin_key in dependencies:
                    del dependencies[plugin_key]
                    print(f"  Removed plugin {plugin_key} from dependencies.")
    else:
        print("Invalid mode. Use 'dev' or 'prod'.")
        return

    with open(pyproject_path, "w") as file:
        file.write(tomlkit.dumps(toml_content))


def update_pyproject_toml(pyproject_path, mode):
    """Switch between development and production mode in pyproject.toml."""
    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} does not exist.")
        return

    with open(pyproject_path, "r") as file:
        toml_content = tomlkit.parse(file.read())

    repo_path = resolve_repo_path()
    project_name = os.path.basename(os.path.dirname(pyproject_path))

    dependencies = toml_content["tool"]["poetry"]["dependencies"]
    prod_dependency_key = "provisioner-shared"
    prod_dependency_pattern = r"^#?\s*provisioner-shared\s*=\s*\"\^.+?\""

    if mode == "dev":
        # Comment out the production dependency if it exists
        for key, value in dependencies.items():
            if (
                key == prod_dependency_key
                and isinstance(value, str)
                and re.match(prod_dependency_pattern, f'{key} = "{value}"')
            ):
                dependencies[key] = tomlkit.comment(f'{key} = "{value}"')

                # Add the development dependency as an inline table
                dev_dependency = tomlkit.inline_table()
                dev_dependency["path"] = f"{repo_path}/provisioner_shared"
                dev_dependency["develop"] = True
                dependencies[prod_dependency_key] = dev_dependency

                print(f"Switched {project_name} to development mode.")

            if key == prod_dependency_key and isinstance(value, tomlkit.items.InlineTable):
                print(f"{project_name} is already in dev mode.")

    elif mode == "prod":
        # Search for the comment and extract the version
        for key, value in dependencies.items():
            # inline table refers to dev mode dictionary
            if key == "provisioner-shared" and isinstance(value, tomlkit.items.InlineTable):
                # Extract the comment
                comment = value.trivia.comment
                if comment and "# provisioner-shared = " in comment:
                    # Extract the version from the comment
                    version = comment.split(" = ")[1].strip('"').strip()
                    # Remove the comment from the original dependency
                    del dependencies[key]
                    # Replace the dependency with the extracted version
                    dependencies[key] = version
                    print(f"Switched {project_name} to production mode.")
                    break

            elif key == "provisioner-shared" and isinstance(value, str):
                print(f"{project_name} is already in prod mode.")
    else:
        print("Invalid mode. Use 'dev' or 'prod'.")
        return

    with open(pyproject_path, "w") as file:
        file.write(tomlkit.dumps(toml_content))


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
    runtime_path = os.path.join(repo_path, "provisioner")
    plugins_path = os.path.join(repo_path, "plugins")

    print()
    print(f"Repository path..: {repo_path}")
    print(f"Runtime path.....: {runtime_path}")
    print(f"Plugins path.....: {plugins_path}")
    print()

    if not os.path.exists(runtime_path):
        print(f"Error: Runtime directory '{runtime_path}' does not exist.")
        return

    if not os.path.exists(plugins_path):
        print(f"Error: Plugins directory '{plugins_path}' does not exist.")
        return

    # Update the monorepo and runtime pyproject.toml files
    monorepo_pyproject_path = os.path.join(repo_path, "pyproject.toml")
    update_root_pyproject_toml(monorepo_pyproject_path, mode)

    # Update the runtime pyproject.toml file
    runtime_pyproject_path = os.path.join(runtime_path, "pyproject.toml")
    update_pyproject_toml(runtime_pyproject_path, mode)

    # Update the plugins pyproject.toml files
    for folder in os.listdir(plugins_path):
        folder_path = os.path.join(plugins_path, folder)
        if os.path.isdir(folder_path) and folder.endswith("_plugin"):
            pyproject_path = os.path.join(folder_path, "pyproject.toml")
            update_pyproject_toml(pyproject_path, mode)


def main():
    parser = argparse.ArgumentParser(
        description="Switch between development and production modes in pyproject.toml for plugins."
    )
    parser.add_argument("mode", choices=["dev", "prod"], help="Mode to switch to: 'dev' or 'prod'.")
    args = parser.parse_args()

    process_plugins(args.mode)
    print()


if __name__ == "__main__":
    main()
