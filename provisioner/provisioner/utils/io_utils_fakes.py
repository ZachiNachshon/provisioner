#!/usr/bin/env python3

from unittest.mock import MagicMock

from provisioner.infra.context import Context
from provisioner.test_lib.faker import TestFakes
from provisioner.utils.io_utils import IOUtils


class FakeIOUtils(TestFakes, IOUtils):

    def __init__(self, ctx: Context):
        TestFakes.__init__(self)
        IOUtils.__init__(self, ctx)

    @staticmethod
    def create(ctx: Context) -> "FakeIOUtils":
        fake = FakeIOUtils(ctx=ctx)
        fake.create_directory_fn = MagicMock(side_effect=fake.create_directory_fn)
        fake.copy_file_fn = MagicMock(side_effect=fake.copy_file_fn)
        fake.copy_directory_fn = MagicMock(side_effect=fake.copy_directory_fn)
        fake.write_file_fn = MagicMock(side_effect=fake.write_file_fn)
        fake.delete_file_fn = MagicMock(side_effect=fake.delete_file_fn)
        fake.read_file_safe_fn = MagicMock(side_effect=fake.read_file_safe_fn)
        fake.write_symlink_fn = MagicMock(side_effect=fake.write_symlink_fn)
        fake.read_symlink_fn = MagicMock(side_effect=fake.read_symlink_fn)
        fake.get_symlink_real_path_fn = MagicMock(side_effect=fake.get_symlink_real_path_fn)
        fake.remove_symlink_fn = MagicMock(side_effect=fake.remove_symlink_fn)
        fake.symlink_exists_fn = MagicMock(side_effect=fake.symlink_exists_fn)
        fake.file_exists_fn = MagicMock(side_effect=fake.file_exists_fn)
        fake.is_archive_fn = MagicMock(side_effect=fake.is_archive_fn)
        fake.unpack_archive_fn = MagicMock(side_effect=fake.unpack_archive_fn)
        fake.set_file_permissions_fn = MagicMock(side_effect=fake.set_file_permissions_fn)
        return fake

    def create_directory_fn(self, folder_path: str) -> bool:
        return self.trigger_side_effect("create_directory_fn", folder_path)

    def copy_file_fn(self, from_path: str, to_path: str) -> bool:
        return self.trigger_side_effect("copy_file_fn", from_path, to_path)

    def copy_directory_fn(self, from_path: str, to_path: str) -> bool:
        return self.trigger_side_effect("copy_directory_fn", from_path, to_path)

    def write_file_fn(self, content: str, file_name: str, dir_path: str = None, executable: bool = False) -> str:
        return self.trigger_side_effect("write_file_fn", content, file_name, dir_path, executable)

    def delete_file_fn(self, file_path: str) -> bool:
        return self.trigger_side_effect("delete_file_fn", file_path)

    def read_file_safe_fn(self, file_path: str) -> str:
        return self.trigger_side_effect("read_file_safe_fn", file_path)

    def write_symlink_fn(self, file_path: str, symlink_path: str) -> bool:
        return self.trigger_side_effect("write_symlink_fn", file_path, symlink_path)

    def read_symlink_fn(self, symlink_path: str) -> str:
        return self.trigger_side_effect("read_symlink_fn", symlink_path)

    def get_symlink_real_path_fn(self, symlink_path: str) -> str:
        return self.trigger_side_effect("get_symlink_real_path_fn", symlink_path)

    def remove_symlink_fn(self, symlink_path: str) -> bool:
        return self.trigger_side_effect("remove_symlink_fn", symlink_path)

    def symlink_exists_fn(self, symlink_path: str) -> bool:
        return self.trigger_side_effect("symlink_exists_fn", symlink_path)

    def file_exists_fn(self, file_path: str) -> bool:
        return self.trigger_side_effect("file_exists_fn", file_path)

    def is_archive_fn(self, file_path: str) -> bool:
        return self.trigger_side_effect("is_archive_fn", file_path)

    def unpack_archive_fn(self, file_path: str) -> str:
        return self.trigger_side_effect("unpack_archive_fn", file_path)

    def set_file_permissions_fn(self, file_path: str, permissions_octal: int = 0o111) -> bool:
        return self.trigger_side_effect("set_file_permissions_fn", file_path, permissions_octal)
