#!/usr/bin/env python3

from typing import List
from provisioner.colors import colors
from provisioner.config.domain.config import PluginDefinition, ProvisionerConfig
from provisioner.config.manager.config_manager import ConfigManager
from provisioner.shared.collaborators import CoreCollaborators
import typer

collaboratos: CoreCollaborators = None

def append_plugins_cmd_to_cli(app: typer.Typer, cli_group_name: str, cols: CoreCollaborators):
    global collaboratos
    collaboratos = cols

    # Create the CLI structure
    plugins_cli_app = typer.Typer()
    app.add_typer(
        plugins_cli_app,
        name="plugins",
        invoke_without_command=True,
        no_args_is_help=True,
        # rich_help_panel=cli_group_name,
        help="Plugins management",
    )

    list_plugins_cli_app = typer.Typer()
    plugins_cli_app.add_typer(
        list_plugins_cli_app,
        name="list",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=list_locally_installed_plugins,
        help="List locally installed provisioner plugins",
    )

    install_plugins_cli_app = typer.Typer()
    plugins_cli_app.add_typer(
        install_plugins_cli_app,
        name="install",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=install_available_plugins,
        help="Search and install plugins from remote",
    )

    uninstall_plugins_cli_app = typer.Typer()
    plugins_cli_app.add_typer(
        uninstall_plugins_cli_app,
        name="uninstall",
        invoke_without_command=True,
        no_args_is_help=False,
        callback=uninstall_local_plugins,
        help="Select local plugins to uninstall",
    )

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


def install_available_plugins() -> None:
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

def uninstall_local_plugins() -> None:
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
            "provisioner-dev-deps", 
            "provisioner_dev_deps", 
            "provisioner-runtime", 
            "provisioner_runtime", 
            "provisioner-features-lib",
            "provisioner_features_lib"
        ],
        debug=True,
    )