#!/usr/bin/env python3

import importlib
import subprocess
from types import ModuleType
from typing import Callable, List, Optional

from loguru import logger


class PackageLoader:
    def __init__(self) -> None:
        pass

    @staticmethod
    def create() -> "PackageLoader":
        # logger.debug(f"Creating package loader")
        return PackageLoader()

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
        for package in packages:
            escaped_package_name = package.replace("-", "_")
            plugin_import_path = f"{escaped_package_name}.{import_path}"

            try:
                logger.debug(f"Importing module {plugin_import_path}")
                plugin_main_module = importlib.import_module(plugin_import_path)
            except Exception as ex:
                logger.error(f"Failed to import module. import_path: {plugin_import_path}, ex: {ex}")
                continue

            try:
                if callback:
                    logger.debug(f"Running module callback on {plugin_import_path}")
                    callback(plugin_main_module)
            except Exception as ex:
                logger.error(f"Import module callback failed. import_path: {plugin_import_path}, ex: {ex}")

    def _load_modules(
        self,
        filter_keyword: str,
        import_path: str,
        exclusions: Optional[List[str]] = [],
        callback: Optional[Callable[[ModuleType], None]] = None,
        debug: Optional[bool] = False,
    ) -> None:

        if not debug:
            logger.remove()

        pip_lines: List[str] = None
        try:
            logger.debug(
                f"About to retrieve pip packages. filter_keyword: {filter_keyword}, exclusions: {str(exclusions)}"
            )
            # Get the list of installed packages
            output = subprocess.check_output(
                [
                    "python3",
                    "-m",
                    "pip",
                    "list",
                    "--no-color",
                    "--no-python-version-warning",
                    "--disable-pip-version-check",
                ]
            )
            # Decode the output and split it into lines
            pip_lines = output.decode("utf-8").split("\n")
        except Exception as ex:
            logger.error(f"Failed to retrieve a list of pip packages, make sure pip is properly installed. ex: {ex}")
            return

        filtered_packages = self._filter_by_keyword(pip_lines, filter_keyword, exclusions)
        logger.debug(f"Successfully retrieved the following packages: {str(filtered_packages)}")

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

    def _create_instance(self, module_name: str, type_name: str) -> object:
        if self._is_module_loaded(module_name):
            type_object = getattr(importlib.import_module(module_name), type_name, None)
            if type_object is None:
                raise ValueError(f"Type {type_name} is not defined")
            # Create an instance of the type object
            return type_object()

        return None

    load_modules_fn = _load_modules
    is_module_loaded_fn = _is_module_loaded
    create_instance_fn = _create_instance
