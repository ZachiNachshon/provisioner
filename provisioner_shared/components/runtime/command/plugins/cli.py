#!/usr/bin/env python3

from typing import List, Optional

import click

from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.colors import colors
from provisioner_shared.components.runtime.config.domain.config import PluginDefinition, ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

collaboratos: CoreCollaborators = None


def append_plugins_cmd_to_cli(root_menu: click.Group, cols: CoreCollaborators):
    global collaboratos
    collaboratos = cols

    @root_menu.group(cls=CustomGroup)
    def plugins():
        """Plugins management"""
        pass

    @plugins.command()
    @cli_modifiers
    def list():
        """List locally installed provisioner plugins"""
        list_locally_installed_plugins()

    @plugins.command()
    @cli_modifiers
    @click.option(
        "--name",
        default=None,
        help="Name of the plugin to install",
        envvar="PROV_PLUGIN_INSTALL_NAME",
        show_default=True,
    )
    def install(name: Optional[str]):
        """Search and install plugins from remote"""
        install_available_plugins(name)

    @plugins.command()
    @cli_modifiers
    @click.option(
        "--name",
        default=None,
        help="Name of the plugin to uninstall",
        envvar="PROV_PLUGIN_UNINSTALL_NAME",
        show_default=True,
    )
    def uninstall(name: Optional[str]):
        """Select local plugins to uninstall"""
        uninstall_plugins(name)


def list_locally_installed_plugins() -> None:
    packages = _try_get_pip_installed_packages()
    output: str = "\n=== Locally Installed Plugins ===\n"
    if packages is None or len(packages) == 0:
        output += "\nNo plugins found."
        collaboratos.printer().print_fn(output)
        return

    prov_cfg: ProvisionerConfig = ConfigManager.instance().get_config()
    for package_name in packages:
        output += "\n"
        pkg_name_escaped = package_name.replace("-", "_")
        if pkg_name_escaped in prov_cfg.plugins_definitions.keys():
            plgn_def = prov_cfg.plugins_definitions.get(pkg_name_escaped, None)
            # TODO: Use Python string template engine in here
            output += f"Name........: {colors.color_text(plgn_def.name, colors.LIGHT_CYAN)}\n"
            output += f"Desc........: {plgn_def.description}\n"
            # output += f"Author......: {plgn_def.author}\n"
            output += f"Maintainer..: {plgn_def.maintainer}\n"

    collaboratos.printer().print_fn(output)


def install_available_plugins(name: Optional[str]) -> None:
    if name is None:
        install_available_plugins_from_prompt()
    else:
        install_available_plugins_from_args(name)


def install_available_plugins_from_args(plgn_name: str) -> None:
    if "provisioner" not in plgn_name:
        raise ValueError("Plugin name must have the 'provisioner_xxx_plugin' format.")

    escaped_pkg_name = plgn_name.replace("_", "-")
    collaboratos.package_loader().install_pip_package_fn(escaped_pkg_name)
    collaboratos.printer().print_fn(f"Plugin {plgn_name} installed successfully.")


def install_available_plugins_from_prompt() -> None:
    packages_from_pip = _try_get_pip_installed_packages()
    packages_from_pip_escaped: List[str] = []
    # Adjust pip plugin name to config plugin name
    for package_name in packages_from_pip:
        escaped_pkg_name = package_name.replace("-", "_")
        packages_from_pip_escaped.append(escaped_pkg_name)

    prov_cfg: ProvisionerConfig = ConfigManager.instance().get_config()
    packages_from_cfg = prov_cfg.plugins_definitions.keys()
    options: List[str] = []
    hash_to_plgn_obj_dict: dict[str, PluginDefinition] = {}

    for package_name in packages_from_cfg:
        # Do not show already installed plugins
        if package_name not in packages_from_pip_escaped:
            plgn_def: PluginDefinition = prov_cfg.plugins_definitions.get(package_name, None)
            display_str = f"{plgn_def.name} - {plgn_def.description} (Maintainer: {plgn_def.maintainer})"
            options.append(display_str)
            hash_to_plgn_obj_dict[hash(display_str)] = plgn_def

    selected_plugins: dict = collaboratos.prompter().prompt_user_multi_selection_fn(
        message="Please select plugins to install", options=options
    )

    for selected_plgn in selected_plugins:
        plgn_def: PluginDefinition = hash_to_plgn_obj_dict.get(hash(selected_plgn), None)
        escaped_pkg_name = plgn_def.package_name.replace("_", "-")
        collaboratos.package_loader().install_pip_package_fn(escaped_pkg_name)
        collaboratos.printer().print_fn(f"Plugin {plgn_def.name} installed successfully.")


def uninstall_plugins(name: Optional[str]) -> None:
    if name is None:
        uninstall_local_plugins_from_prompt()
    else:
        uninstall_local_plugins_from_args(name)


def uninstall_local_plugins_from_args(plgn_name: str) -> None:
    if "provisioner" not in plgn_name:
        raise ValueError("Plugin name must have the 'provisioner_xxx_plugin' format.")

    escaped_pkg_name = plgn_name.replace("_", "-")
    collaboratos.package_loader().uninstall_pip_package_fn(escaped_pkg_name)
    collaboratos.printer().print_fn(f"Plugin {plgn_name} uninstalled successfully.")


def uninstall_local_plugins_from_prompt() -> None:
    packages_from_pip = _try_get_pip_installed_packages()
    if packages_from_pip is None or len(packages_from_pip) == 0:
        collaboratos.printer().print_fn("No installed plugins found.")
        return
    packages_from_pip_escaped: List[str] = []
    # Adjust pip plugin name to config plugin name
    for package_name in packages_from_pip:
        escaped_pkg_name = package_name.replace("-", "_")
        packages_from_pip_escaped.append(escaped_pkg_name)

    prov_cfg: ProvisionerConfig = ConfigManager.instance().get_config()
    options: List[str] = []
    hash_to_plgn_obj_dict: dict[str, PluginDefinition] = {}

    for package_name in packages_from_pip_escaped:
        plgn_def: PluginDefinition = prov_cfg.plugins_definitions.get(package_name, None)
        display_str = f"{plgn_def.name} - {plgn_def.description} (Maintainer: {plgn_def.maintainer})"
        options.append(display_str)
        hash_to_plgn_obj_dict[hash(display_str)] = plgn_def

    selected_plugins: dict = collaboratos.prompter().prompt_user_multi_selection_fn(
        message="Please select plugins to uninstall", options=options
    )

    for selected_plgn in selected_plugins:
        plgn_def: PluginDefinition = hash_to_plgn_obj_dict.get(hash(selected_plgn), None)
        escaped_pkg_name = plgn_def.package_name.replace("_", "-")
        collaboratos.package_loader().uninstall_pip_package_fn(escaped_pkg_name)
        collaboratos.printer().print_fn(f"Plugin {plgn_def.name} uninstalled successfully.")


def _try_get_pip_installed_packages():
    return collaboratos.package_loader().get_pip_installed_packages_fn(
        filter_keyword="provisioner",
        exclusions=[
            "provisioner-shared",
            "provisioner_shared",
            "provisioner-runtime",
            "provisioner_runtime",
        ],
        debug=True,
    )
