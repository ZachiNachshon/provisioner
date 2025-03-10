import sys
import re
from typing import Optional

def get_cli_argument_value(arg_name: str) -> str | None:
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

def is_cli_argument_present(arg_name: str, short: Optional[str] = None) -> bool:
    """
    Checks if a given CLI argument (full name or shorthand) exists in the CLI arguments.
    """
    exists = any(arg.startswith(arg_name) for arg in sys.argv)
    if not exists and len(short) > 0:
        return any(arg.startswith(short) for arg in sys.argv)
    return exists
