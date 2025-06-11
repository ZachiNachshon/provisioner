#!/usr/bin/env python3

import importlib
import pathlib
import subprocess
from types import ModuleType
from typing import Callable, List, Optional

from loguru import logger

from provisioner_shared.components.runtime.cli.modifiers import PackageManager
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.io_utils import IOUtils
from provisioner_shared.components.runtime.utils.process import Process
from provisioner_shared.components.runtime.utils.pypi_registry import PyPiRegistry
from provisioner_shared.components.runtime.utils.version_compatibility import VersionCompatibility

RUNTIME_PACKAGE_NAME = "provisioner-runtime"


class PackageLoader:
    _ctx: Context = None
    _io_utils: IOUtils = None
    _process: Process = None
    _pkg_mgr: PackageManager = None
    _pypi_registry: PyPiRegistry = None

    def __init__(self, ctx: Context, io_utils: IOUtils, process: Process, pypi: PyPiRegistry) -> None:
        self._ctx = ctx
        self._pkg_mgr = ctx.get_package_manager()
        self._io_utils = io_utils
        self._process = process
        self._pypi_registry = pypi
        self._cached_runtime_version: Optional[str] = None

    @staticmethod
    def create(ctx: Context, io_utils: IOUtils, process: Process, pypi: PyPiRegistry) -> "PackageLoader":
        logger.debug(f"Creating package loader using {ctx._pkg_mgr} as package manager")
        return PackageLoader(ctx, io_utils, process, pypi)

    def _filter_by_keyword(self, pip_lines: List[str], filter_keyword: str, exclusions: List[str]) -> List[str]:
        filtered_packages = []
        for line in pip_lines:
            if line.startswith(filter_keyword):
                package = line.split()[0]
                if package not in exclusions:
                    filtered_packages.append(package)
        return filtered_packages

    def _import_modules(
        self, packages: List[str], import_path: str, callback: Optional[Callable[[ModuleType], None]] = None
    ) -> None:
        if packages is None:
            logger.warning("No packages to import")
            return

        for package in packages:
            escaped_package_name = package.replace("-", "_")
            plugin_import_path = f"{escaped_package_name}.{import_path}"

            try:
                logger.debug(f"Importing module {plugin_import_path}")
                plugin_main_module = importlib.import_module(plugin_import_path)
            except Exception as ex:
                print(f"Failed to import module. import_path: {plugin_import_path}, ex: {ex}")
                continue

            try:
                if callback:
                    logger.debug(f"Running module callback on {plugin_import_path}")
                    callback(plugin_main_module)
            except Exception as ex:
                logger.error(f"Import module callback failed. import_path: {plugin_import_path}, ex: {ex}")

    def _get_pip_installed_packages(
        self,
        filter_keyword: str,
        exclusions: Optional[List[str]] = [],
        debug: Optional[bool] = False,
        enable_version_filtering: Optional[bool] = True,
        runtime_version: Optional[str] = None,
    ) -> List[str]:

        if not debug:
            logger.remove()

        pip_lines: List[str] = None
        try:
            logger.debug(
                f"About to retrieve pip packages. filter_keyword: {filter_keyword}, exclusions: {str(exclusions)}"
            )
            pip_install_cmd: List[str] = self._get_pip_cmd()
            # Get the list of installed packages
            output = subprocess.check_output(
                pip_install_cmd
                + [
                    "list",
                    "--no-color",
                ]
            )
            # Decode the output and split it into lines
            pip_lines = output.decode("utf-8").split("\n")
            # for line in pip_lines:
            #     print(line)
            #     logger.debug(line)
        except Exception as ex:
            logger.error(
                f"Failed to retrieve a list of pip packages, make sure {self._pkg_mgr} is properly installed. ex: {ex}"
            )
            return

        # Exclude provisioner-runtime and provisioner_runtime
        exclusions_with_underscores = [exclusion.replace("-", "_") for exclusion in exclusions]
        exclusions_with_underscores.extend(exclusions)
        filtered_packages = self._filter_by_keyword(pip_lines, filter_keyword, exclusions_with_underscores)

        logger.debug(
            f"Found {len(filtered_packages)} packages to check for compatibility. packages: {str(filtered_packages)}"
        )

        # Apply version compatibility filtering if enabled
        if enable_version_filtering and runtime_version:
            logger.debug(f"Applying version compatibility filtering for runtime version: {runtime_version}")
            filtered_packages = VersionCompatibility.filter_compatible_plugins(filtered_packages, runtime_version)

        logger.debug(f"Successfully retrieved the following packages: {str(filtered_packages)}")
        return filtered_packages

    def _load_modules(
        self,
        filter_keyword: str,
        import_path: str,
        exclusions: Optional[List[str]] = [],
        callback: Optional[Callable[[ModuleType], None]] = None,
        debug: Optional[bool] = False,
        enable_version_filtering: Optional[bool] = True,
        runtime_version: Optional[str] = None,
    ) -> None:

        filtered_packages = self._get_pip_installed_packages(
            filter_keyword=filter_keyword,
            exclusions=exclusions,
            debug=debug,
            enable_version_filtering=enable_version_filtering,
            runtime_version=runtime_version,
        )

        self._import_modules(filtered_packages, import_path, callback)

    def _is_module_loaded(self, module_name: str) -> bool:
        result = False
        try:
            importlib.import_module(module_name)
            result = True
            # print(f"Module {module_name} imported successfully!")
        except ModuleNotFoundError:
            # print(f"Module {module_name} not found.")
            pass
        except ImportError:
            # print(f"ImportError occurred: {e}")
            pass
        return result

    def _create_module_instance(self, module_name: str, type_name: str) -> object:
        if self._is_module_loaded(module_name):
            type_object = getattr(importlib.import_module(module_name), type_name, None)
            if type_object is None:
                raise ValueError(f"Type {type_name} is not defined")
            # Create an instance of the type object
            return type_object()

        return None

    def _install_pip_package(self, package_name: str) -> None:
        try:
            logger.debug(f"About to install pip package. name: {package_name}")
            pip_cmd: List[str] = self._get_pip_cmd()
            subprocess.check_output(
                pip_cmd
                + [
                    "install",
                    package_name,
                    "--no-color",
                ]
            )
        except Exception as ex:
            logger.error(f"Failed to install pip package. name: {package_name}, ex: {ex}")
            raise ex

    def _uninstall_pip_package(self, package_name: str) -> None:
        try:
            logger.debug(f"About to uninstall pip package. name: {package_name}")
            pip_install_cmd: List[str] = self._get_pip_cmd()
            subprocess.check_output(
                pip_install_cmd
                + [
                    "uninstall",
                    package_name,
                    "-y",
                    "--no-color",
                ]
            )
        except Exception as ex:
            logger.error(f"Failed to uninstall pip package. name: {package_name}, ex: {ex}")
            raise ex

    def _get_pip_cmd(self) -> List[str]:
        # return ["python3", "-m", "pip"]
        match self._pkg_mgr:
            case PackageManager.PIP:
                logger.debug("Using pip as package manager")
                return ["python3", "-m", "pip", "--disable-pip-version-check"]
            case PackageManager.UV:
                logger.debug("Using uv as package manager")
                return ["uv", "pip", "--no-python-downloads"]
            # case PackageManager.VENV:
            #     logger.debug("Using venv as package manager")
            #     return ["./.venv/bin/pip"]
            case _:
                raise ValueError(f"Unsupported package manager: {self._pkg_mgr}")

    # This method currently works only with Poetry since it is the only package manager
    # that supports bundling multiple projects into a single sdist/wheel using a poetry plugin
    def _build_sdists(self, project_paths: List[str], target_dist_folder: str):
        """
        Runs `poetry build` on multiple projects and copies built distributions.

        :param project_paths: List of paths to Poetry projects in the monorepo.
        :param target_dist_folder: Path to the folder where built distributions should be copied.
        """
        target_dist_folder = pathlib.Path(target_dist_folder)
        self._io_utils.create_directory_fn(target_dist_folder)  # Ensure target folder exists

        for project_path in project_paths:
            project_path = pathlib.Path(project_path).resolve()
            if not (project_path / "pyproject.toml").exists():
                print(f"Skipping {project_path}: No pyproject.toml found.")
                continue

            # Determine expected distribution filename
            print(f"Checking {project_path} version for distribution...")
            output = self._process.run_fn(
                args=["poetry", "version"],
                working_dir=project_path,
                fail_msg=f"Failed to install dependencies with Poetry. project: {project_path}",
                fail_on_error=True,
            )

            package_name, version = output.strip().split()
            expected_tarball = f"{package_name}-{version}.tar.gz"
            dist_path = project_path / "dist" / expected_tarball

            # Check if distribution already exists in target folder
            # if (target_dist_folder / expected_tarball).exists():
            #     print(f"Skipping build for {package_name}, already exists in {target_dist_folder}")
            #     continue

            # Build package with `poetry build`
            print(f"Building {package_name} in {project_path}...")
            self._process.run_fn(
                args=["poetry", "build-project", "-f", "sdist"],
                working_dir=project_path,
                fail_msg=f"Failed to install dependencies with Poetry. project: {project_path}",
                fail_on_error=True,
            )

            # Copy distribution to target folder
            if dist_path.exists():
                self._io_utils.copy_file_fn(dist_path, target_dist_folder)
                print(f"Copied {expected_tarball} to {target_dist_folder}")
            else:
                print(f"Error: Expected tarball {expected_tarball} not found in {project_path / 'dist'}!")

    def _get_runtime_version_from_pip(self) -> Optional[str]:
        """
        Try to get runtime version from installed runtime package.

        Returns:
            Runtime version string if found, None otherwise
        """
        pip_cmd = self._get_pip_cmd()
        runtime_version = VersionCompatibility.get_package_version_from_pip(pip_cmd, RUNTIME_PACKAGE_NAME)
        if runtime_version:
            logger.debug(f"Found runtime version from pip: {runtime_version}")
            return runtime_version
        return None

    def _get_runtime_version_from_local_files(self) -> Optional[str]:
        """
        Try to get runtime version from local version.txt file (for development).

        Returns:
            Runtime version string if found, None otherwise
        """
        try:
            import pathlib

            # Try different potential paths for the runtime
            potential_paths = [
                "provisioner/resources/version.txt",
                "../provisioner/resources/version.txt",
                "../../provisioner/resources/version.txt",
                # Also try relative to the current package
                pathlib.Path(__file__).parent.parent.parent.parent.parent / "provisioner" / "resources" / "version.txt",
            ]

            for path in potential_paths:
                version = self._io_utils.read_file_safe_fn(path)
                if version:
                    logger.debug(f"Found runtime version from local file {path}: {version}")
                    version = version.strip()
                    return version

        except Exception as e:
            logger.debug(f"Error reading local version file: {e}")

        return None

    def _get_runtime_version_from_pypi(self) -> Optional[str]:
        """
        Try to get runtime version from PyPI as fallback (runtime package ONLY).

        Returns:
            Runtime version string if found, None otherwise
        """
        logger.debug("Local runtime not found, trying to get latest version from PyPI")
        pypi_version = self._pypi_registry._get_package_version_fn(RUNTIME_PACKAGE_NAME)
        if pypi_version:
            logger.debug(f"Found runtime version from PyPI: {pypi_version}")
            return pypi_version
        return None

    def _get_runtime_version(self) -> Optional[str]:
        """
        Get the current runtime version, trying multiple methods.

        Returns:
            Runtime version string if found, None otherwise
        """
        if self._cached_runtime_version is not None:
            return self._cached_runtime_version

        # Method 1: Try to get from installed runtime package
        runtime_version = self._get_runtime_version_from_pip()
        if runtime_version:
            self._cached_runtime_version = runtime_version
            return runtime_version

        # Method 2: Try to get from local version.txt file (for development)
        runtime_version = self._get_runtime_version_from_local_files()
        if runtime_version:
            self._cached_runtime_version = runtime_version
            return runtime_version

        # Method 3: Try to get latest version from PyPI as fallback (runtime package ONLY)
        runtime_version = self._get_runtime_version_from_pypi()
        if runtime_version:
            self._cached_runtime_version = runtime_version
            return runtime_version

        logger.warning("Could not determine runtime version from any source")
        return None

    def _load_modules_with_auto_version_check(
        self,
        filter_keyword: str,
        import_path: str,
        exclusions: Optional[List[str]] = [],
        callback: Optional[Callable[[ModuleType], None]] = None,
        debug: Optional[bool] = False,
    ) -> None:
        """
        Load modules with automatic runtime version detection and compatibility checking.
        This is the preferred method for loading plugins as it automatically applies version filtering.
        """
        runtime_version = self._get_runtime_version()

        self._load_modules(
            filter_keyword=filter_keyword,
            import_path=import_path,
            exclusions=exclusions,
            callback=callback,
            debug=debug,
            enable_version_filtering=True,
            runtime_version=runtime_version,
        )

    load_modules_fn = _load_modules
    load_modules_with_version_check_fn = _load_modules_with_auto_version_check
    import_modules_fn = _import_modules
    is_module_loaded_fn = _is_module_loaded
    create_module_instance_fn = _create_module_instance
    get_pip_installed_packages_fn = _get_pip_installed_packages
    install_pip_package_fn = _install_pip_package
    uninstall_pip_package_fn = _uninstall_pip_package
    build_sdists_fn = _build_sdists
    get_runtime_version_fn = _get_runtime_version
