#!/usr/bin/env python3

from typing import Optional
from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.paths import Paths


class FakePaths(TestFakes, Paths):
    def __init__(self, ctx: Context):
        TestFakes.__init__(self)
        Paths.__init__(self, ctx=ctx)

    @staticmethod
    def create(ctx: Context) -> "FakePaths":
        fake = FakePaths(ctx=ctx)
        fake.get_home_directory_fn = MagicMock(side_effect=fake.get_home_directory_fn)
        fake.get_current_directory_fn = MagicMock(side_effect=fake.get_current_directory_fn)
        fake.get_path_from_exec_module_root_fn = MagicMock(side_effect=fake.get_path_from_exec_module_root_fn)
        fake.get_path_abs_to_module_root_fn = MagicMock(side_effect=fake.get_path_abs_to_module_root_fn)
        fake.get_path_relative_from_module_root_fn = MagicMock(side_effect=fake.get_path_relative_from_module_root_fn)
        fake.get_file_path_from_python_package = MagicMock(side_effect=fake.get_file_path_from_python_package)
        fake.get_dir_path_from_python_package = MagicMock(side_effect=fake.get_dir_path_from_python_package)
        return fake

    def get_home_directory_fn(self) -> bool:
        return self.trigger_side_effect("get_home_directory_fn")

    def get_current_directory_fn(self) -> bool:
        return self.trigger_side_effect("get_current_directory_fn")

    def get_path_from_exec_module_root_fn(self, relative_path: Optional[str] = None) -> bool:
        return self.trigger_side_effect("get_path_from_exec_module_root_fn", relative_path)

    def get_path_abs_to_module_root_fn(self, package_name: str, relative_path: Optional[str] = None) -> bool:
        return self.trigger_side_effect("get_path_abs_to_module_root_fn", package_name, relative_path)

    def get_path_relative_from_module_root_fn(self, package_name: str, relative_path: Optional[str] = None) -> bool:
        return self.trigger_side_effect("get_path_relative_from_module_root_fn", package_name, relative_path)

    def get_file_path_from_python_package(self, package: str, filename: str) -> bool:
        return self.trigger_side_effect("get_file_path_from_python_package", package, filename)

    def get_dir_path_from_python_package(self, package: str, dirname: str) -> bool:
        return self.trigger_side_effect("get_dir_path_from_python_package", package, dirname)
