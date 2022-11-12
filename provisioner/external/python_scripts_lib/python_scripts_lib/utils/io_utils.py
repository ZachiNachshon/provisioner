#!/usr/bin/env python3

import os
import stat
import tempfile
from pathlib import Path
from shutil import copy2
from typing import Optional

from loguru import logger

from ..infra.context import Context


class IOUtils:
    def __init__(self, ctx: Context) -> None:
        pass

    @staticmethod
    def create(ctx: Context) -> "IOUtils":
        logger.debug(f"Creating IO utils...")
        return IOUtils(ctx)

    def _get_home_directory(self):
        # Python 3.5+
        return str(Path.home())

    def _get_current_directory(self):
        # Python 3.5+
        return str(Path.cwd())

    def _relative_path_to_abs_path(self, relative_path: str):
        curr_file_path = os.path.dirname(os.path.realpath("__file__"))
        file_name = os.path.join(curr_file_path, relative_path)
        return os.path.abspath(os.path.realpath(file_name))

    def _create_directory(self, folder_path):
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            os.makedirs(folder_path, exist_ok=True)

    def _copy_file_or_dir(self, from_path: str, to_path: str):
        copy2(from_path, to_path)

    def _write_file(
        self, content: str, file_name: str, dir_path: Optional[str] = None, executable: Optional[bool] = False
    ) -> str:
        path = dir_path if dir_path else tempfile.mkdtemp(prefix="python-lib-files-")
        path = "{}/{}".format(path, file_name)
        try:
            with open(path, "w+") as opened_file:
                opened_file.write(content)
                opened_file.close()
                logger.debug("Created file. path: {}".format(path))
                if executable:
                    file_stats = os.stat(path)
                    os.chmod(path=path, mode=file_stats.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        except Exception as error:
            logger.error("Error = {}\nFailed to create file. path: {}".format(error, path))
            raise error

        return path

    def _delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        else:
            logger.warning("File does not exists, cannot delete. path: {}", file_path)
            return False

    def _read_file_safe(self, file_path: str):
        content = None
        try:
            with open(file_path, "r+") as opened_file:
                content = opened_file.read()
                opened_file.close()
                logger.debug("Read file successfully. path: {}".format(file_path))

        except Exception as error:
            # Debug log level on purpose since read failures might be legit in some cases
            logger.debug(error)

        return content

    def _write_symlink(self, file_path, symlink_path):
        os.symlink(src=file_path, dst=symlink_path)
        logger.debug("Created symlink. path: {}".format(symlink_path))

    def _read_symlink(self, symlink_path):
        real_path = self._get_symlink_real_path(symlink_path)
        return self._read_file_safe(real_path)

    def _get_symlink_real_path(self, symlink_path):
        return os.readlink(symlink_path) if os.path.islink(symlink_path) else symlink_path

    def _remove_symlink(self, symlink_path):
        if self._is_empty(symlink_path) and self._is_symlink(symlink_path):
            os.remove(symlink_path)
            logger.debug("Deleted symlink. path: {}".format(symlink_path))

    def _symlink_exists(self, symlink_path):
        return os.path.exists(symlink_path)

    def _file_exists(self, file_path):
        return os.path.exists(file_path)

    def _is_empty(self, file_path):
        return os.path.isfile(file_path) and os.stat(file_path).st_size == 0

    def _is_symlink(self, file_path):
        return os.path.islink(file_path)

    get_home_directory_fn = _get_home_directory
    get_current_directory_fn = _get_current_directory
    relative_path_to_abs_path_fn = _relative_path_to_abs_path
    create_directory_fn = _create_directory
    copy_file_or_dir_fn = _copy_file_or_dir
    write_file_fn = _write_file
    delete_file_fn = _delete_file
    read_file_safe_fn = _read_file_safe
    write_symlink_fn = _write_symlink
    read_symlink_fn = _read_symlink
    get_symlink_real_path_fn = _get_symlink_real_path
    remove_symlink_fn = _remove_symlink
    symlink_exists_fn = _symlink_exists
    file_exists_fn = _file_exists
