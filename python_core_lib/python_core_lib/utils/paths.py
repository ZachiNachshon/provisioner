#!/usr/bin/env python3

import os
import pathlib
import sys
from importlib import resources
from pathlib import Path
from typing import Optional

from loguru import logger

from python_core_lib.infra.context import Context


class Paths:

    _verbose: bool
    _dry_run: bool

    def __init__(self, ctx: Context) -> None:
        self._verbose = ctx.is_verbose()
        self._dry_run = ctx.is_dry_run()

    @staticmethod
    def create(ctx: Context) -> "Paths":
        logger.debug("Creating Paths utils...")
        return Paths(ctx)

    def _get_home_directory(self) -> str:
        # Python 3.5+
        return str(Path.home())

    def _get_current_directory(self) -> str:
        # Python 3.5+
        return str(Path.cwd())

    def _get_path_from_exec_module_root(self, relative_path: Optional[str] = None) -> str:
        """
        Return the root folder path of the current executing project, requires a __file__ parameter
        so the starting CWD will be the actual Python file within the virtual env or pip-pkg
        and not from this IO utility file
        """
        exec_path = self._get_exec_main_path()
        return self._calculate_static_file_path_from_project(exec_path, relative_path)

    def _get_path_abs_to_module_root(self, package_name, relative_path: Optional[str] = None) -> str:
        """
        Package name is the __name_ variable so the path resolution would be from the
        calling imported file package
        """
        # path = pkgutil.get_data(package_name, relative_path)
        path = os.path.dirname(sys.modules[package_name].__file__)
        return self._calculate_static_file_path_from_project(path, relative_path)

    def _get_path_relative_from_module_root(self, package_name, relative_path: Optional[str] = None) -> str:
        """
        Package is the __name_ variable so the path resolution would be from the
        calling imported file package
        """
        # path = pkgutil.get_data(package_name, relative_path)
        path = os.path.dirname(sys.modules[package_name].__file__)
        module_root = self._calculate_static_file_path_from_project(path)
        module_name = os.path.basename(module_root)
        if relative_path:
            return (
                f"{module_name}{relative_path}" if relative_path.startswith("/") else f"{module_name}/{relative_path}"
            )
        return module_name

    def _calculate_static_file_path_from_project(self, file_path, relative_path: Optional[str] = None) -> str:
        result_path = None
        parent_path = pathlib.Path(file_path).parent
        while True:
            basename = os.path.basename(parent_path)
            if os.path.exists(f"{parent_path}/pyproject.toml") or os.path.exists(f"{parent_path}/setup.py"):
                result_path = parent_path
                break
            elif basename == "/" or len(basename) == 0:
                break
            parent_path = parent_path.parent

        if result_path and relative_path:
            return (
                f"{result_path}{relative_path}" if relative_path.startswith("/") else f"{result_path}/{relative_path}"
            )
        return result_path

    # def _relative_path_to_abs_path(self, relative_path: str) -> str:
    #     curr_file_path = os.path.dirname(os.path.realpath("__file__"))
    #     file_name = os.path.join(curr_file_path, relative_path)
    #     return os.path.abspath(os.path.realpath(file_name))

    def _get_exec_main_path(self):
        """
        This is an internal method, not exposed from this utility class
        """
        try:
            sFile = os.path.abspath(sys.modules["__main__"].__file__)
        except Exception:
            sFile = sys.executable
        return os.path.dirname(sFile)

    def _get_file_path_from_python_package(self, package: str, filename: str) -> str:
        if self._dry_run:
            return "DRY_RUN_RESPONSE"
        return resources.path(package=package, resource=filename)

    def _get_dir_path_from_python_package(self, package: str, dirname: str) -> str:
        if self._dry_run:
            return "DRY_RUN_RESPONSE"
        return resources.files(package).joinpath(dirname)

    get_home_directory_fn = _get_home_directory
    get_current_directory_fn = _get_current_directory
    get_path_from_exec_module_root_fn = _get_path_from_exec_module_root
    get_path_abs_to_module_root_fn = _get_path_abs_to_module_root
    get_path_relative_from_module_root_fn = _get_path_relative_from_module_root
    get_file_path_from_python_package = _get_file_path_from_python_package
    get_dir_path_from_python_package = _get_dir_path_from_python_package
    # relative_path_to_abs_path_fn = _relative_path_to_abs_path
