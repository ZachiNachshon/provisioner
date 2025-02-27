#!/usr/bin/env python3
import argparse
import os
import re

import tomlkit

PROVISIONER_SHARED_DEP_NAME = "provisioner_shared"
FORMAT_ALREADY_IN_DEV_MODE = " [DEV MODE] {}"
FORMAT_ALREADY_IN_PROD_MODE = " [PROD MODE] {}"
FORMAT_SWITCHED_PROD_TO_DEV_MODE = " [PROD->DEV] {} ({})"
FORMAT_SWITCHED_DEV_TO_PROD_MODE = " [DEV->PROD] {}"

def print_switched_dev_mode(project_name: str, path: str):
    print(FORMAT_SWITCHED_PROD_TO_DEV_MODE.format(project_name, path))

def print_switched_prod_mode(project_name: str):
    print(FORMAT_SWITCHED_DEV_TO_PROD_MODE.format(project_name))

def print_already_in_dev_mode(project_name: str):
    print(FORMAT_ALREADY_IN_DEV_MODE.format(project_name))

def print_already_in_prod_mode(project_name: str):
    print(FORMAT_ALREADY_IN_PROD_MODE.format(project_name))

def resolve_repo_path():
    """Resolve the absolute path of the repository."""
    current_dir = os.path.abspath(os.getcwd())
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, ".git")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise RuntimeError("Repository root not found.")

REPOSITORY_PATH = resolve_repo_path()

def generate_toml_dev_dependency(dep_local_path: str):
    dev_dependency = tomlkit.inline_table()
    dev_dependency["path"] = dep_local_path
    dev_dependency["develop"] = True
    return dev_dependency


def read_pyproject_toml_file(pyproject_path: str):
    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} does not exist.")
        raise FileNotFoundError
    
    with open(pyproject_path, "r") as file:
        toml_content = tomlkit.parse(file.read())

    return toml_content


def write_pyproject_toml_file(pyproject_path: str, toml_content: str):
    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} does not exist.")
        raise FileNotFoundError
    
    with open(pyproject_path, "w") as file:
        file.write(tomlkit.dumps(toml_content))


def update_as_prod_dependency(toml_dependencies, dep_name: str, project_name: str, force: bool = False):
    if force and dep_name in toml_dependencies:
        # Remove dependency
        del toml_dependencies[dep_name]
        print_switched_prod_mode("[FORCED] " + dep_name)
    
    # Other pyproject.toml files should have the dependencies as versioned rather than with absolute paths
    else:
        # Search for the comment and extract the version
        for key, value in toml_dependencies.items():
            # inline table refers to dev mode dictionary
            if key == dep_name and isinstance(value, tomlkit.items.InlineTable):
                # Extract the comment
                comment = value.trivia.comment
                if comment and f"# {dep_name} = " in comment:
                    # Extract the version from the comment
                    version = comment.split(" = ")[1].strip('"').strip()
                    if version:
                        # Remove the comment from the original dependency
                        del toml_dependencies[key]
                        # Replace the dependency with the extracted version
                        toml_dependencies[key] = version
                        print_switched_prod_mode(dep_name)
                        break
                    else:
                        raise ValueError(f"Invalid version for {dep_name} in {project_name} dependencies")
                else:
                    raise ValueError(f"Project {project_name} is missing the production version comment for {dep_name} dependency")

            elif key == dep_name and isinstance(value, str):
                print_already_in_prod_mode(dep_name)


def update_as_dev_dependency(toml_dependencies, dep_abs_path: str, force: bool = False):
    dep_name = os.path.basename(dep_abs_path)
    regx_pattern = r"^#?\s*" + dep_name + r"\s*=\s*\"\^.+?\""

    # Add the development dependency as an inline table
    dev_dependency = generate_toml_dev_dependency(dep_abs_path)

    if force and dep_name in toml_dependencies:
        # Remove dependency
        toml_dependencies[dep_name] = dev_dependency
        print_switched_dev_mode("[FORCED] " + dep_name, dev_dependency)
        return

    # Comment out the production dependency if it exists
    found = False
    for key, value in toml_dependencies.items():
        # If key exists already as a production dependency, comment it and add new dev dependency
        if (
            key == dep_name
            and isinstance(value, str)
            and re.match(regx_pattern, f'{key} = "{value}"')
        ):
            toml_dependencies[key] = tomlkit.comment(f'{key} = "{value}"')
            toml_dependencies[dep_name] = dev_dependency
            found = True
            print_switched_dev_mode(dep_name, dev_dependency)
            
        # If key exists already as a dev dependency, do not add again
        elif key == dep_name and isinstance(value, tomlkit.items.InlineTable):
            found = True
            print_already_in_dev_mode(dep_name)

    # If key does not exist, add it as a new dev dependency
    if not found:
        toml_dependencies[dep_name] = dev_dependency
        print_already_in_dev_mode(dep_name)


def switch_toml_to_dev_mode(toml_dependencies, project_name: str, with_plugins_deps: bool = False, force: bool = False):
    print(f"\nSwitching {project_name} to development mode...")
    dep_abs_path = os.path.join(REPOSITORY_PATH, PROVISIONER_SHARED_DEP_NAME)
    update_as_dev_dependency(toml_dependencies, dep_abs_path, force)

    # Maybe update plugins as development dependencies
    if with_plugins_deps:
        plugins_path = os.path.join(REPOSITORY_PATH, "plugins")
        if not os.path.exists(plugins_path):
            print(f"Could not identify valid plugins dependencies path: {plugins_path}")
            return
    
        # Add or update all plugins as development dependencies
        for plugin_folder in os.listdir(plugins_path):
            plugin_path = os.path.join(plugins_path, plugin_folder)
            if os.path.isdir(plugin_path) and plugin_folder.endswith("_plugin"):
                update_as_dev_dependency(toml_dependencies, plugin_path, force)
    

def switch_toml_to_prod_mode(toml_dependencies, project_name: str, with_plugins_deps: bool = False, force: bool = False):
    print(f"\nSwitching {project_name} to production mode...")
    update_as_prod_dependency(toml_dependencies, PROVISIONER_SHARED_DEP_NAME, project_name, force)

    # Root pyproject.toml file prod mode should not have any path based or versioned dependencies
    if with_plugins_deps:
        plugins_path = os.path.join(REPOSITORY_PATH, "plugins")
        if not os.path.exists(plugins_path):
            print(f"Could not identify valid plugins dependencies path: {plugins_path}")
            return

        for plugin_folder in os.listdir(plugins_path):
            plugin_path = os.path.join(plugins_path, plugin_folder)
            if os.path.isdir(plugin_path) and plugin_folder.endswith("_plugin"):
                update_as_prod_dependency(toml_dependencies, plugin_folder, project_name, force)


def update_plugin_pyproject_toml(pyproject_path, mode: str, force: bool = False):
    project_name = os.path.basename(os.path.dirname(pyproject_path))
    toml_file_content = read_pyproject_toml_file(pyproject_path)
    toml_dependencies = toml_file_content["tool"]["poetry"]["dependencies"]

    if mode == "dev":
        switch_toml_to_dev_mode(toml_dependencies, project_name, with_plugins_deps=False, force=force)
    elif mode == "prod":
        switch_toml_to_prod_mode(toml_dependencies, project_name, with_plugins_deps=False, force=force)
    else:
        print("Invalid mode. Use 'dev' or 'prod'.")
        return
    write_pyproject_toml_file(pyproject_path, toml_file_content)


def update_runtime_pyproject_toml(pyproject_path, mode: str, force: bool = False):
    project_name = os.path.basename(os.path.dirname(pyproject_path))
    toml_file_content = read_pyproject_toml_file(pyproject_path)
    toml_dependencies = toml_file_content["tool"]["poetry"]["dependencies"]

    if mode == "dev":
        switch_toml_to_dev_mode(toml_dependencies, project_name, with_plugins_deps=False, force=force)
    elif mode == "prod":
        switch_toml_to_prod_mode(toml_dependencies, project_name, with_plugins_deps=False, force=force)
    else:
        print("Invalid mode. Use 'dev' or 'prod'.")
        return
    write_pyproject_toml_file(pyproject_path, toml_file_content)


def update_root_pyproject_toml(pyproject_path, mode: str, force: bool = False):
    project_name = "ROOT"
    toml_file_content = read_pyproject_toml_file(pyproject_path)
    toml_dependencies = toml_file_content["tool"]["poetry"]["dependencies"]

    if mode == "dev":
        switch_toml_to_dev_mode(toml_dependencies, project_name, with_plugins_deps=True, force=force)
    elif mode == "prod":
        switch_toml_to_prod_mode(toml_dependencies, project_name, with_plugins_deps=True, force=True)
    else:
        print("Invalid mode. Use 'dev' or 'prod'.")
        return
    write_pyproject_toml_file(pyproject_path, toml_file_content)


def replace_line(content, old_line_start, new_line):
    """Replace a line in the content based on its start string."""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(old_line_start):
            lines[i] = new_line
            break
    return "\n".join(lines)


def process_project_files(mode: str, force: bool):
    """Iterate through plugins and update their pyproject.toml files."""
    repo_path = resolve_repo_path()
    runtime_path = os.path.join(repo_path, "provisioner")
    plugins_path = os.path.join(repo_path, "plugins")

    print()
    print(f"Mode.............: {mode}")
    print(f"Repository path..: {repo_path}")
    print(f"Runtime path.....: {runtime_path}")
    print(f"Plugins path.....: {plugins_path}")
    print()

    # Update the monorepo and runtime pyproject.toml files
    monorepo_pyproject_path = os.path.join(repo_path, "pyproject.toml")
    update_root_pyproject_toml(monorepo_pyproject_path, mode, force)

    if not os.path.exists(runtime_path):
        print(f"Error: Runtime directory '{runtime_path}' does not exist.")
        return

    # Update the runtime pyproject.toml file
    runtime_pyproject_path = os.path.join(runtime_path, "pyproject.toml")
    update_runtime_pyproject_toml(runtime_pyproject_path, mode, force)

    if not os.path.exists(plugins_path):
        print(f"Error: Plugins directory '{plugins_path}' does not exist.")
        return

    # Update the plugins pyproject.toml files
    for folder in os.listdir(plugins_path):
        folder_path = os.path.join(plugins_path, folder)
        if os.path.isdir(folder_path) and folder.endswith("_plugin"):
            plugins_pyproject_path = os.path.join(folder_path, "pyproject.toml")
            update_plugin_pyproject_toml(plugins_pyproject_path, mode, force)


def main():
    parser = argparse.ArgumentParser(
        description="Switch between development and production modes in pyproject.toml for plugins."
    )
    parser.add_argument("mode", choices=["dev", "prod", "docker"], help="Mode to switch to: 'dev', 'prod' or 'docker'.")
    parser.add_argument("--force", action="store_true", help="Ignore existing deps and force switch to selected mode.")
    args = parser.parse_args()

    process_project_files(mode=args.mode, force=args.force)
    print()


if __name__ == "__main__":
    main()
