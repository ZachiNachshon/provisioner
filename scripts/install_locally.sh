#!/bin/bash
# Usage: ./install_locally.sh [install|uninstall] [runtime|plugin PLUGIN_NAME] [wheel|sdist]

# Function to display help
show_help() {
  echo "Usage: $0 <install|uninstall> [runtime|plugin PLUGIN_NAME] [wheel|sdist]"
  echo ""
  echo "Actions:"
  echo "  install     Build and install packages"
  echo "  uninstall   Remove installed packages"
  echo ""
  echo "Installation types:"
  echo "  runtime     Process the core runtime packages (provisioner_shared and provisioner)"
  echo "  plugin      Process a specific plugin (requires PLUGIN_NAME parameter)"
  echo ""
  echo "Package format (only for install action):"
  echo "  wheel       Build and install wheel packages (default)"
  echo "  sdist       Build and install source distribution packages"
  echo ""
  echo "Examples:"
  echo "  $0 install runtime             # Install runtime packages as wheels"
  echo "  $0 install runtime sdist       # Install runtime packages as source distributions"
  echo "  $0 install plugin examples     # Install a plugin as wheel"
  echo "  $0 install plugin examples     # Install a plugin as wheel"
  echo "  $0 uninstall plugin examples   # Uninstall a plugin"
  echo "  $0 uninstall runtime           # Uninstall runtime packages"
  exit 1
}

# Default values
INSTALL_TYPE="runtime"
PKG_FORMAT="wheel"
BUILD_ARG="-f wheel"

# Parse action argument
if [[ "$1" == "install" ]]; then
  ACTION="install"
  shift
elif [[ "$1" == "uninstall" ]]; then
  ACTION="uninstall"
  shift
else
  # No valid action specified, show help
  show_help
fi

# Parse installation type
if [[ "$1" == "runtime" || "$1" == "" ]]; then
  INSTALL_TYPE="runtime"
elif [[ "$1" == "plugin" ]]; then
  INSTALL_TYPE="plugin"
  if [[ -z "$2" ]]; then
    echo "Error: plugin name is required. Usage: ./install_locally.sh [install|uninstall] plugin PLUGIN_NAME [wheel|sdist]"
    exit 1
  fi
  PLUGIN_NAME="$2"
  shift
else
  echo "Unknown installation type: $1"
  show_help
fi

# Check for package format (only needed for install)
if [[ "$ACTION" == "install" && "$2" == "sdist" ]]; then
  PKG_FORMAT="sdist"
  BUILD_ARG="-f sdist"
fi

# Function to install a package
install_package() {
  local pkg_dir="$1"
  local pkg_name="$2"
  
  echo -e "\n========= INSTALLING: $pkg_name =============="
  pip uninstall -y "$pkg_name" || true
  
  # Save current directory
  local CURRENT_DIR=$(pwd)
  cd "$pkg_dir"
  # poetry build-project $BUILD_ARG
  poetry build $BUILD_ARG
  cd "$CURRENT_DIR"
  
  # Install the generated package
  if [[ "$PKG_FORMAT" == "wheel" ]]; then
    pip install "$pkg_dir/dist/$pkg_name"*.whl
  else
    pip install "$pkg_dir/dist/$pkg_name"*.tar.gz
  fi
}

# Function to uninstall a package
uninstall_package() {
  local pkg_name="$1"
  
  echo -e "\n========= UNINSTALLING: $pkg_name =============="
  pip uninstall -y "$pkg_name" || true
}

# Process packages based on action and installation type
if [[ "$ACTION" == "install" ]]; then
  # Install packages
  if [[ "$INSTALL_TYPE" == "runtime" ]]; then
    install_package "provisioner_shared" "provisioner_shared"
    install_package "provisioner" "provisioner_runtime"
  else
    # Install plugin
    plugin_path="plugins/provisioner_${PLUGIN_NAME}_plugin"
    install_package "$plugin_path" "provisioner_${PLUGIN_NAME}_plugin"
  fi
  echo -e "\nInstallation complete!"
else
  # Uninstall packages
  if [[ "$INSTALL_TYPE" == "runtime" ]]; then
    uninstall_package "provisioner_runtime"
    uninstall_package "provisioner_shared"
  else
    # Uninstall plugin
    uninstall_package "provisioner_${PLUGIN_NAME}_plugin"
  fi
  echo -e "\nUninstallation complete!"
fi