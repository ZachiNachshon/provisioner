#!/usr/bin/env python3

from typing import List, Optional

import click

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.colors import colors
from provisioner_shared.components.runtime.config.domain.config import PluginDefinition, ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.version_compatibility import VersionCompatibility


def append_plugins_cmd_to_cli(root_menu: click.Group, collaborators: CoreCollaborators):

    @root_menu.group(cls=CustomGroup)
    def plugins():
        """Plugins management"""
        pass

    @plugins.command()
    @cli_modifiers
    def list():
        """List locally installed provisioner plugins"""
        list_locally_installed_plugins(collaborators)

    @plugins.command()
    @cli_modifiers
    @click.option(
        "--show-incompatible",
        is_flag=True,
        default=False,
        help="Also show plugins that are incompatible with current runtime version",
        envvar="PROV_PLUGIN_SHOW_INCOMPATIBLE",
    )
    def compatibility(show_incompatible: bool):
        """Show plugin compatibility information with current runtime version"""
        show_plugin_compatibility(collaborators, show_incompatible)

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
        install_available_plugins(name, collaborators)

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
        uninstall_plugins(name, collaborators)


def list_locally_installed_plugins(collaborators: CoreCollaborators) -> None:
    packages = _try_get_pip_installed_packages(collaborators)
    output: str = "\n=== Locally Installed Plugins ===\n"
    if packages is None or len(packages) == 0:
        output += "\nNo plugins found."
        collaborators.printer().print_fn(output)
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

    collaborators.printer().print_fn(output)


def install_available_plugins(name: Optional[str], collaborators: CoreCollaborators) -> None:
    if name is None:
        install_available_plugins_from_prompt(collaborators)
    else:
        install_available_plugins_from_args(name, collaborators)


def install_available_plugins_from_args(plgn_name: str, collaborators: CoreCollaborators) -> None:
    if "provisioner" not in plgn_name:
        raise ValueError("Plugin name must have the 'provisioner_xxx_plugin' format.")

    escaped_pkg_name = plgn_name.replace("_", "-")
    collaborators.package_loader().install_pip_package_fn(escaped_pkg_name)
    collaborators.printer().print_fn(f"Plugin {plgn_name} installed successfully.")


def install_available_plugins_from_prompt(collaborators: CoreCollaborators) -> None:
    # Check if there are already installed plugins
    packages_from_pip = _try_get_pip_installed_packages(collaborators)
    packages_from_pip_escaped: List[str] = []

    # Adjust pip plugin name to config plugin name
    for package_name in packages_from_pip:
        escaped_pkg_name = package_name.replace("-", "_")
        packages_from_pip_escaped.append(escaped_pkg_name)

    prov_cfg: ProvisionerConfig = ConfigManager.instance().get_config()
    # The available plugins are the ones defined in the provisioner runtime config
    packages_from_cfg = prov_cfg.plugins_definitions.keys()
    options: List[str] = []
    hash_to_plgn_obj_dict: dict[str, PluginDefinition] = {}

    for package_name in packages_from_cfg:
        # Do not suggest to install already installed plugins
        if package_name not in packages_from_pip_escaped:
            plgn_def: PluginDefinition = prov_cfg.plugins_definitions.get(package_name, None)
            display_str = f"{plgn_def.name} - {plgn_def.description} (Maintainer: {plgn_def.maintainer})"
            options.append(display_str)
            hash_to_plgn_obj_dict[hash(display_str)] = plgn_def

    if len(options) == 0:
        collaborators.printer().print_fn("No plugins found or plugins already installed.")
        return

    selected_plugins: dict = collaborators.prompter().prompt_user_multi_selection_fn(
        message="Please select plugins to install", options=options
    )

    for selected_plgn in selected_plugins:
        plgn_def: PluginDefinition = hash_to_plgn_obj_dict.get(hash(selected_plgn), None)
        escaped_pkg_name = plgn_def.package_name.replace("_", "-")
        collaborators.package_loader().install_pip_package_fn(escaped_pkg_name)
        collaborators.printer().print_fn(f"Plugin {plgn_def.name} installed successfully.")


def uninstall_plugins(name: Optional[str], collaborators: CoreCollaborators) -> None:
    if name is None:
        uninstall_local_plugins_from_prompt(collaborators)
    else:
        uninstall_local_plugins_from_args(name, collaborators)


def uninstall_local_plugins_from_args(plgn_name: str, collaborators: CoreCollaborators) -> None:
    if "provisioner" not in plgn_name:
        raise ValueError("Plugin name must have the 'provisioner_xxx_plugin' format.")

    escaped_pkg_name = plgn_name.replace("_", "-")
    collaborators.package_loader().uninstall_pip_package_fn(escaped_pkg_name)
    collaborators.printer().print_fn(f"Plugin {plgn_name} uninstalled successfully.")


def uninstall_local_plugins_from_prompt(collaborators: CoreCollaborators) -> None:
    packages_from_pip = _try_get_pip_installed_packages(collaborators)
    if packages_from_pip is None or len(packages_from_pip) == 0:
        collaborators.printer().print_fn("No installed plugins found.")
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

    selected_plugins: dict = collaborators.prompter().prompt_user_multi_selection_fn(
        message="Please select plugins to uninstall", options=options
    )

    for selected_plgn in selected_plugins:
        plgn_def: PluginDefinition = hash_to_plgn_obj_dict.get(hash(selected_plgn), None)
        escaped_pkg_name = plgn_def.package_name.replace("_", "-")
        collaborators.package_loader().uninstall_pip_package_fn(escaped_pkg_name)
        collaborators.printer().print_fn(f"Plugin {plgn_def.name} uninstalled successfully.")


def show_plugin_compatibility(collaborators: CoreCollaborators, show_incompatible: bool = False) -> None:
    """Show plugin compatibility information with current runtime version"""
    runtime_version = collaborators.package_loader().get_runtime_version_fn()

    if not runtime_version:
        collaborators.printer().print_fn("⚠️  Could not determine runtime version")
        return

    # Get all installed plugins (without version filtering)
    all_packages = _try_get_pip_installed_packages(collaborators, enable_version_filtering=False)

    if not all_packages or len(all_packages) == 0:
        collaborators.printer().print_fn("No plugins found.")
        return

    output = "\n=== Plugin Compatibility Report ===\n\n"
    output += f"Runtime Version: {colors.color_text(runtime_version, colors.LIGHT_CYAN)}\n\n"

    prov_cfg: ProvisionerConfig = ConfigManager.instance().get_config()
    compatible_count = 0
    incompatible_count = 0

    for package_name in all_packages:
        pkg_name_escaped = package_name.replace("-", "_")
        plgn_def = prov_cfg.plugins_definitions.get(pkg_name_escaped, None)

        if not plgn_def:
            continue

        is_compatible = VersionCompatibility.is_plugin_compatible(package_name, runtime_version)

        if is_compatible:
            compatible_count += 1
            status_icon = "✅"
            status_color = colors.GREEN
        else:
            incompatible_count += 1
            status_icon = "❌"
            status_color = colors.RED

        # Only show incompatible plugins if requested
        if not is_compatible and not show_incompatible:
            continue

        output += f"{status_icon} {colors.color_text(plgn_def.name, colors.LIGHT_CYAN)}\n"
        output += f"   Package: {package_name}\n"
        output += f"   Status: {colors.color_text('Compatible' if is_compatible else 'Incompatible', status_color)}\n"

        # Try to get the compatibility range
        try:
            import importlib.util

            normalized_name = package_name.replace("-", "_")
            spec = importlib.util.find_spec(normalized_name)
            if spec and spec.origin:
                from pathlib import Path

                plugin_path = Path(spec.origin).parent
                version_range = VersionCompatibility.read_plugin_compatibility(str(plugin_path))
                if version_range:
                    output += f"   Required Runtime: {version_range}\n"
                else:
                    output += f"   Required Runtime: {colors.color_text('Not specified (assumes compatible)', colors.YELLOW)}\n"
        except Exception:
            output += f"   Required Runtime: {colors.color_text('Could not determine', colors.YELLOW)}\n"

        output += "\n"

    # Summary
    output += f"Summary: {colors.color_text(str(compatible_count), colors.GREEN)} compatible, "
    output += f"{colors.color_text(str(incompatible_count), colors.RED)} incompatible\n"

    if incompatible_count > 0 and not show_incompatible:
        output += "\nUse --show-incompatible to see incompatible plugins\n"

    collaborators.printer().print_fn(output)


def _try_get_pip_installed_packages(collaborators: CoreCollaborators, enable_version_filtering: bool = True):
    runtime_version = None
    if enable_version_filtering:
        runtime_version = collaborators.package_loader().get_runtime_version_fn()

    return collaborators.package_loader().get_pip_installed_packages_fn(
        filter_keyword="provisioner",
        exclusions=[
            "provisioner-shared",
            "provisioner-runtime",
        ],
        debug=True,
        enable_version_filtering=enable_version_filtering,
        runtime_version=runtime_version,
    )
