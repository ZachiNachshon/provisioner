#!/usr/bin/env python3

import pathlib
from typing import List

from python_core_lib.infra.context import Context
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.io_utils import IOUtils


class FakeIOUtils(IOUtils):

    __registered_read_file_safe_paths: dict[str, str] = None
    __registered_is_archive: dict[str, bool] = None
    __registered_unpack_archive: dict[str, str] = None
    __registered_set_file_permissions: List[str] = None
    __registered_write_symlink: List[str] = None

    __mocked_is_archive: dict[str, bool] = None
    __mocked_unpack_archive: dict[str, str] = None  # return value: archive parent folder path

    def __init__(self, ctx: Context):
        super().__init__(ctx)
        self.__registered_read_file_safe_paths = {}
        self.__registered_is_archive = {}
        self.__registered_unpack_archive = {}
        self.__registered_set_file_permissions = []
        self.__registered_write_symlink = []
        self.__mocked_is_archive = {}
        self.__mocked_unpack_archive = {}

    @staticmethod
    def _create_fake(ctx: Context) -> "FakeIOUtils":
        io = FakeIOUtils(ctx)
        io.read_file_safe_fn = lambda file_path: io._read_file_safe_selector(file_path)
        io.write_file_fn = lambda content, file_name, dir_path=None, executable=False: "/test/script/file/{}".format(
            file_name
        )
        io.create_directory_fn = lambda folder_path: folder_path
        io.delete_file_fn = lambda file_path: True
        io.file_exists_fn = lambda file_path: True
        io.is_archive_fn = lambda file_path: io._register_is_archive(file_path)
        io.unpack_archive_fn = lambda file_path: io._register_unpack_archive(file_path)
        io.set_file_permissions_fn = lambda file_path, permissions_octal=0o111: io._register_set_file_permissions(
            file_path, permissions_octal
        )
        io.write_symlink_fn = lambda file_path, symlink_path: io._register_write_symlink(file_path, symlink_path)
        io.copy_file_fn = lambda from_path, to_path: None
        io.copy_directory_fn = lambda from_path, to_path: None
        return io

    @staticmethod
    def create(ctx: Context) -> "FakeIOUtils":
        return FakeIOUtils._create_fake(ctx)

    def register_file_read(self, file_path: str, expected_output: str):
        # When opting to use the FakeIOUtils instead of mocking via @mock.patch, we'll override the read function
        self.__registered_read_file_safe_paths[file_path] = expected_output

    def _read_file_safe_selector(self, file_path: str) -> str:
        if file_path not in self.__registered_read_file_safe_paths:
            raise LookupError(f"Fake IO read file path is not defined. name: {file_path}")
        return self.__registered_read_file_safe_paths.get(file_path)

    def _register_is_archive(self, file_path: str) -> bool:
        is_archive = self.__mocked_is_archive.get(file_path, False)
        self.__registered_is_archive[file_path] = is_archive
        return is_archive

    def assert_is_archive(self, file_path: str, is_archive: bool) -> None:
        if file_path not in self.__registered_is_archive:
            raise FakeEnvironmentAssertionError(
                f"IOUtils expected to check if a filepath is of type archive but it never triggered. file_path: {file_path}"
            )
        elif is_archive != self.__registered_is_archive[file_path]:
            raise FakeEnvironmentAssertionError(
                "IOUtils expected a file to have a specific archive state but it never matched.\n"
                + f"Actual:\n{self.__registered_is_archive[file_path]}\n"
                + f"Expected:\n{is_archive}"
            )

    def mock_is_archive(self, file_path: str, is_archive: bool) -> None:
        self.__mocked_is_archive[file_path] = is_archive

    def _register_unpack_archive(self, file_path: str) -> str:
        parent_folder_path = self.__mocked_unpack_archive.get(file_path, None)
        self.__registered_unpack_archive[file_path] = (
            parent_folder_path if parent_folder_path else str(pathlib.Path(file_path).parent)
        )
        return self.__registered_unpack_archive[file_path]

    def assert_unpack_archive(self, file_path: str) -> None:
        if file_path not in self.__registered_unpack_archive:
            raise FakeEnvironmentAssertionError(
                "IOUtils expected to unpack an archive but it never triggered.\n"
                + f"Actual:\n{self.__registered_unpack_archive.keys()}\n"
                + f"Expected:\n{file_path}"
            )

    def _register_set_file_permissions(self, file_path: str, permissions_octal: int) -> str:
        self.__registered_set_file_permissions.append(f"{file_path}__{permissions_octal}")
        return file_path

    def assert_set_file_permissions(self, file_path: str, permissions_octal: int) -> None:
        if f"{file_path}__{permissions_octal}" not in self.__registered_set_file_permissions:
            raise FakeEnvironmentAssertionError(
                "IOUtils expected to set file permissions but it never triggered.\n"
                + f"Actual:\n{self.__registered_set_file_permissions}\n"
                + f"Expected:\n{file_path}__{permissions_octal}"
            )

    def _register_write_symlink(self, file_path: str, symlink_path: str) -> str:
        self.__registered_write_symlink.append(f"{file_path}__{symlink_path}")
        return symlink_path

    def assert_write_symlink(self, file_path: str, symlink_path: str) -> None:
        if f"{file_path}__{symlink_path}" not in self.__registered_write_symlink:
            raise FakeEnvironmentAssertionError(
                "IOUtils expected to write symlink but it never triggered.\n"
                + f"Actual:\n{self.__registered_write_symlink}\n"
                + f"Expected:\n{file_path}__{symlink_path}"
            )
