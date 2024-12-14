#!/usr/bin/env python3

import argparse

import tomlkit


def update_dependency_version(file_path, package_name, new_version):
    """
    Update the version of a specific dependency in pyproject.toml.

    :param file_path: Path to the pyproject.toml file.
    :param package_name: The name of the dependency to update.
    :param new_version: The new version to set for the dependency.
    """
    try:
        # Read the pyproject.toml file
        with open(file_path, "r") as file:
            pyproject_content = tomlkit.parse(file.read())

        # Access the dependencies section
        dependencies = pyproject_content["tool"]["poetry"]["dependencies"]

        # Update the version if the package exists
        if package_name in dependencies:
            dependencies[package_name] = new_version
            print(f"Updated {package_name} to version {new_version}.")
        else:
            print(f"Package {package_name} not found in dependencies.")

        # Write the updated pyproject.toml back to the file
        with open(file_path, "w") as file:
            file.write(tomlkit.dumps(pyproject_content))

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a dependency version in pyproject.toml.")
    parser.add_argument("--file_path", type=str, required=True, help="Path to the pyproject.toml file.")
    parser.add_argument("--package_name", type=str, required=True, help="The name of the dependency to update.")
    parser.add_argument("--new_version", type=str, required=True, help="The new version to set for the dependency.")

    args = parser.parse_args()

    update_dependency_version(args.file_path, args.package_name, args.new_version)
