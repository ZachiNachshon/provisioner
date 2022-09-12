#!/usr/bin/env python3

from .io_utils import IOUtils


class FakeIOUtils(IOUtils):

    registered_read_file_safe_paths: dict[str, str] = {}

    @staticmethod
    def _create_fake() -> "FakeIOUtils":
        io = FakeIOUtils()
        io.read_file_safe_fn = lambda file_path: io._read_file_safe_selector(file_path)
        io.write_file_fn = lambda content, file_name, dir_path=None, executable=False: "/test/script/file/{}".format(
            file_name
        )
        io.create_directory_fn = lambda folder_path: folder_path
        io.delete_file_fn = lambda file_path: True
        io.file_exists_fn = lambda file_path: True
        return io

    @staticmethod
    def create() -> "FakeIOUtils":
        return FakeIOUtils._create_fake()

    def register_file_read(self, file_path: str, expected_output: str):
        # When opting to use the FakeIOUtils instead of mocking via @mock.patch, we'll override the read function
        self.registered_read_file_safe_paths[file_path] = expected_output

    def _read_file_safe_selector(self, file_path: str) -> str:
        if file_path not in self.registered_read_file_safe_paths:
            raise LookupError("Fake IO read file path is not defined. name: " + file_path)
        return self.registered_read_file_safe_paths.get(file_path)
