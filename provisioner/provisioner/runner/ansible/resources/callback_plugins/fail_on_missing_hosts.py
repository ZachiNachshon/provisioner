# Taken from https://gist.github.com/jjshoe/ace3070906e5bc5cc432
# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys

from ansible.plugins.callback import CallbackBase

RED = "\033[0;31m"
NONE = "\033[0m"
GO_UP_ONE_LINE = "\033[1A"
DELETE_LINE_TO_BEGINNING = "\033[K"


class CallbackModule(CallbackBase):
    """
    This callback module exists non-zero if no hosts match
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "no_hosts_match_exit_non_zero"
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        super(CallbackModule, self).__init__()

    def playbook_on_stats(self, stats):
        found_stats = False

        for key in ["ok", "failures", "dark", "changed", "skipped"]:
            if len(getattr(stats, key)) > 0:
                found_stats = True
                break

        if found_stats is False:
            print(f"{RED}[ERROR] Could not connect to selected hosts or none supplied/matched{NONE}")
            sys.exit(10)
