#!/usr/bin/env python3

from python_core_lib.infra.context import Context
from python_core_lib.utils.paths import Paths

HOME_DIR_DEFAULT = "/test-home"
CURRENT_DIR_DEFAULT = "/test-home/test-user"
PATH_EXEC_MODULE_ROOT_DEFAULT = f"{CURRENT_DIR_DEFAULT}/test-exec-root"
PATH_ABS_TO_MODULE_ROOT = f"{CURRENT_DIR_DEFAULT}/test-module-root"
PATH_RELATIVE_FROM_MODULE_ROOT = "test-module-root"


class FakePaths(Paths):

    home_dir: str = HOME_DIR_DEFAULT
    current_dir: str = CURRENT_DIR_DEFAULT
    path_exec_module_root: str = PATH_EXEC_MODULE_ROOT_DEFAULT
    path_abs_module_root: str = PATH_ABS_TO_MODULE_ROOT
    path_relative_module_root: str = PATH_RELATIVE_FROM_MODULE_ROOT

    def __init__(self, ctx: Context):
        super().__init__(ctx)

    @staticmethod
    def _create_fake(ctx: Context) -> "FakePaths":
        paths = FakePaths(ctx)
        paths.get_home_directory_fn = lambda: paths.home_dir
        paths.get_current_directory_fn = lambda: paths.current_dir
        paths.get_path_from_exec_module_root_fn = (
            lambda relative_path=None: paths.append_relative_path(paths.path_exec_module_root, relative_path)
            if relative_path
            else paths.path_exec_module_root
        )
        paths.get_path_abs_to_module_root_fn = (
            lambda package_name, relative_path=None: paths.append_relative_path(
                paths.path_abs_module_root, relative_path
            )
            if relative_path
            else paths.path_abs_module_root
        )
        paths.get_path_relative_from_module_root_fn = (
            lambda package_name, relative_path=None: paths.append_relative_path(
                paths.path_relative_module_root, relative_path
            )
            if relative_path
            else paths.path_relative_module_root
        )
        paths.get_file_path_from_python_package = lambda package_name: paths.append_relative_path(
            package_name.replace(".", "/"), ""
        )
        paths.relative_path_to_abs_path_fn = lambda relative_path: ""
        return paths

    @staticmethod
    def create(ctx: Context) -> "FakePaths":
        return FakePaths._create_fake(ctx)

    def append_relative_path(self, path: str, relative_path: str) -> str:
        if not relative_path.startswith("/"):
            relative_path += f"/{relative_path}"
        return f"{path}{relative_path}"

    def register_custom_paths(
        self,
        home_dir: str = HOME_DIR_DEFAULT,
        current_dir: str = CURRENT_DIR_DEFAULT,
        path_exec_module_root: str = PATH_EXEC_MODULE_ROOT_DEFAULT,
        path_abs_module_root: str = PATH_ABS_TO_MODULE_ROOT,
        path_relative_module_root: str = PATH_RELATIVE_FROM_MODULE_ROOT,
    ):

        self.home_dir = home_dir
        self.current_dir = current_dir
        self.path_exec_module_root = path_exec_module_root
        self.path_abs_module_root = path_abs_module_root
        self.path_relative_module_root = path_relative_module_root
