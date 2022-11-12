#!/usr/bin/env python3

import platform
from typing import Optional

from ..errors.cli_errors import OsArchInvalidFlagException

MAC_OS = "darwin"
LINUX = "linux"
WINDOWS = "windows"


class OsArch:
    os: str = ""
    os_release: str = ""
    arch: str = ""

    def __init__(self, os: Optional[str] = None, arch: Optional[str] = None, os_release: Optional[str] = None):
        result = platform.uname()
        self.os = os if os else result.system.lower()
        self.arch = arch if arch else result.machine.lower()
        self.os_release = os_release if os_release else result.release.lower()

    def is_darwin(self):
        return self.os == MAC_OS

    def is_linux(self):
        return self.os == LINUX

    def is_windows(self):
        return self.os == WINDOWS

    def as_pair(self, mapping: Optional[dict[str, str]] = None) -> str:
        """
        Return OS_ARCH pairs and allow to set a different architecture name
        e.g. linux_X86_64 --> linux_amd64
        """
        result: str = "{os}_{arch}".format(os=self.os, arch=self.arch)
        if mapping and self.arch in mapping:
            result = "{os}_{arch}".format(os=self.os, arch=mapping.get(self.arch))
        return result

    @staticmethod
    def from_string(os_arch: str) -> "OsArch":
        splitted = os_arch.split("_")
        if len(splitted) < 2:
            raise OsArchInvalidFlagException(f"Invalid os_arch flag value. os_arch: {os_arch}")

        os = splitted[0].lower()
        if not OsArch._is_valid_os_str(os):
            raise OsArchInvalidFlagException(f"Invalid os flag. os: {os}")

        arch = splitted[1].lower()
        if not OsArch._is_valid_arch_str(arch):
            raise OsArchInvalidFlagException(f"Invalid arch flag. arch: {arch}")

        return OsArch(os=os, arch=arch.lower())

    @staticmethod
    def _is_valid_os_str(os: str) -> bool:
        return os in (MAC_OS, LINUX, WINDOWS)

    @staticmethod
    def _is_valid_arch_str(arch: str) -> bool:
        # return arch in ()
        return True
