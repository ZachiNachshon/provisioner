#!/usr/bin/env python3


from ..infra.context import Context
from ..utils.io_utils import IOUtils
from ..utils.process import Process


class SystemReader:

    io: IOUtils
    process: Process

    def __init__(self, process: Process, io: IOUtils) -> None:
        self.process = process
        self.io = io

    def _read_os_release(self, ctx: Context) -> str:
        result = "OS is not supported"

        if ctx.os_arch.is_darwin():
            result = self.process.run_fn(args=["system_profiler", "SPSoftwareDataType"])

        elif ctx.os_arch.is_linux():
            os_release_path = "/etc/os-release"
            if self.io.file_exists_fn(os_release_path):
                result = self.io.read_file_safe_fn(os_release_path)
            else:
                raise Exception("Cannot locate Linux file. path: {}".format(os_release_path))

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError(result)

        return result

    def _read_hardware_cpu(self, ctx: Context) -> str:
        result = "OS is not supported"

        if ctx.os_arch.is_darwin():
            result = self.process.run_fn(args=["system_profiler", "SPHardwareDataType"])

        elif ctx.os_arch.is_linux():
            proc_cpu_info_path = "/proc/cpuinfo"
            if self.io.file_exists_fn(proc_cpu_info_path):
                result = self.io.read_file_safe_fn(proc_cpu_info_path)
            else:
                raise Exception("Linux file/proc is missing. path: {}".format(proc_cpu_info_path))

            lscpu_tool_name = "lscpu"
            if self.process.is_tool_exist_fn(lscpu_tool_name):
                result += "\n"
                result += self.process.run_fn(args=[lscpu_tool_name])
            else:
                raise Exception("Linux utility is missing. name: {}".format(lscpu_tool_name))

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError(result)

        return result

    def _read_hardware_mem(self, ctx: Context) -> str:
        result = "OS is not supported"

        if ctx.os_arch.is_darwin():
            result = self.process.run_fn(args=["system_profiler", "SPHardwareDataType"])
            result += "\n"
            result += self.process.run_fn(args=["system_profiler", "SPDisplaysDataType"])

        elif ctx.os_arch.is_linux():
            proc_mem_info_path = "/proc/meminfo"
            if self.io.file_exists_fn(proc_mem_info_path):
                result = self.io.read_file_safe_fn(proc_mem_info_path)
            else:
                raise Exception("Linux file/proc is missing. path: {}".format(proc_mem_info_path))

            vcgencmd_tool_name = "vcgencmd"
            if self.process.is_tool_exist_fn(vcgencmd_tool_name):
                result += "\n"
                result += self.process.run_fn(args=[vcgencmd_tool_name, "get_mem", "gpu"])
            else:
                raise Exception("Linux utility is missing. name: {}".format(vcgencmd_tool_name))

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError(result)

        return result

    def _read_hardware_network(self, ctx: Context) -> str:
        result = "OS is not supported"

        if ctx.os_arch.is_darwin():
            raise NotImplementedError()
        elif ctx.os_arch.is_linux():
            raise NotImplementedError()
        elif ctx.os_arch.is_windows():
            raise NotImplementedError()
        else:
            raise NotImplementedError(result)

        return result

    read_os_release_func = _read_os_release
    read_hardware_cpu_func = _read_hardware_cpu
    read_hardware_mem_func = _read_hardware_mem
    read_hardware_network_func = _read_hardware_network
