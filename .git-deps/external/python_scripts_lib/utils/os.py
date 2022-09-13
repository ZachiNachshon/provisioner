#!/usr/bin/env python3

import platform
from typing import Optional

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
