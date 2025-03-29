import os
from functools import wraps

import pytest


def skip_if_not_in_docker(obj):
    def is_running_in_docker():
        # Check for /.dockerenv (commonly present in Docker)
        if os.path.exists("/.dockerenv"):
            return True
        # Check /proc/1/cgroup for "docker" (if available)
        try:
            with open("/proc/1/cgroup", "r") as f:
                return any("docker" in line or "containerd" in line for line in f)
        except FileNotFoundError:
            pass  # If the file doesn't exist, assume we're not in Docker
        return False

    if not is_running_in_docker():
        if isinstance(obj, type):  # If it's a class
            obj = pytest.mark.skip(reason="Skipping test: Not running inside a Docker container")(obj)
        else:  # If it's a function

            @wraps(obj)
            def wrapper(*args, **kwargs):
                pytest.skip("Skipping test: Not running inside a Docker container")

            return wrapper
    return obj
