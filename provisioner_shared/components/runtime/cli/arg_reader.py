import re
import sys
from typing import Optional

from loguru import logger

from provisioner_shared.components.runtime.cli.modifiers import PackageManager
from provisioner_shared.components.runtime.infra.context import Context


class PreRunArgs:

    def __init__(self) -> None:
        """
        The --dry-run and --verbose flags aren't available on the pre-init phase
        since logger is being set-up after Click is initialized.
        I've added pre Click run env var to control the visiblity of components debug logs
        such as config-loader, package-loader etc..
        """
        self.debug_pre_init: bool = False
        self.maybe_pkg_mgr: Optional[PackageManager] = None

    def handle_pre_click_args(self, ctx: Context) -> "PreRunArgs":
        self._parse_pre_run_args()
        ctx._verbose = self.debug_pre_init
        if not self.debug_pre_init:
            logger.remove()

        if self.maybe_pkg_mgr:
            ctx._pkg_mgr = self.maybe_pkg_mgr

        return self

    def _parse_pre_run_args(self) -> "PreRunArgs":
        self.debug_pre_init = _is_cli_argument_present("--verbose", "-v")
        maybe_pkg_mgr_str = _get_cli_argument_value("--package-manager")
        if maybe_pkg_mgr_str:
            self.maybe_pkg_mgr = PackageManager.from_str(maybe_pkg_mgr_str)


def _get_cli_argument_value(arg_name: str) -> str | None:
    """
    Retrieves the value of a given CLI argument (supports both full and shorthand flags).
    - `--arg value`
    - `--arg=value`
    - `--arg= value`
    - `-a value`
    - `-a=value`
    """
    for i, arg in enumerate(sys.argv):
        # Match '--arg=value' or '--arg= value' or '-a=value'
        match = re.match(rf"{arg_name}=(\s*)(\S+)", arg)
        if match:
            return match.group(2)  # Extract value after '='

        # Match '--arg value' or '-a value'
        if arg == arg_name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]

    return None


def _is_cli_argument_present(arg_name: str, short: Optional[str] = None) -> bool:
    """
    Checks if a given CLI argument (full name or shorthand) exists in the CLI arguments.
    """
    exists = any(arg.startswith(arg_name) for arg in sys.argv)
    if not exists and len(short) > 0:
        return any(arg.startswith(short) for arg in sys.argv)
    return exists
