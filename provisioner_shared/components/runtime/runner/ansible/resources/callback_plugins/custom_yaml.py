# -*- coding: utf-8 -*-
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    author: Unknown (!UNKNOWN)
    name: yaml
    type: stdout
    short_description: yaml-ized Ansible screen output
    description:
        - Ansible output that can be quite a bit easier to read than the
          default JSON formatting.
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout in configuration
"""

import json
import re
import string

import yaml
from ansible.module_utils.common.text.converters import to_text
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.callback import (
    module_response_deepcopy,
    strip_internal_keys,
)
from ansible.plugins.callback.default import CallbackModule as Default


# from http://stackoverflow.com/a/15423007/115478
def should_use_block(value):
    """Returns true if string should be in block format"""
    for c in "\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False


class MyDumper(AnsibleDumper):
    def represent_scalar(self, tag, value, style=None):
        """Uses block style for multi-line strings"""
        if style is None:
            if should_use_block(value):
                style = "|"
                # we care more about readable than accuracy, so...
                # ...no trailing space
                value = value.rstrip()
                # ...and non-printable characters
                value = "".join(x for x in value if x in string.printable or ord(x) >= 0xA0)
                # ...tabs prevent blocks from expanding
                value = value.expandtabs()
                # ...and odd bits of whitespace
                value = re.sub(r"[\x0b\x0c\r]", "", value)
                # ...as does trailing space
                value = re.sub(r" +\n", "\n", value)
            else:
                style = self.default_style
        node = yaml.representer.ScalarNode(tag, value, style=style)
        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node
        return node


class CallbackModule(Default):
    # class CallbackModule(CallbackBase):

    """
    Variation of the Default output which uses nicely readable YAML instead
    of JSON for printing results.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "custom_yaml"

    def __init__(self):
        super(CallbackModule, self).__init__()

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):
        if result.get("_ansible_no_log", False):
            return json.dumps(
                dict(
                    censored="The output has been hidden due to the fact that 'no_log: true' was specified for this result"
                )
            )

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(module_response_deepcopy(result))

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and "invocation" in result:
            del abridged_result["invocation"]

        # remove diff information from screen output
        if self._display.verbosity < 3 and "diff" in result:
            del abridged_result["diff"]

        # remove exception from screen output
        if "exception" in abridged_result:
            del abridged_result["exception"]

        dumped = ""

        # put changed and skipped into a header line
        if "changed" in abridged_result:
            dumped += "changed=" + str(abridged_result["changed"]).lower() + " "
            del abridged_result["changed"]

        if "skipped" in abridged_result:
            dumped += "skipped=" + str(abridged_result["skipped"]).lower() + " "
            del abridged_result["skipped"]

        # if we already have stdout, we don't need stdout_lines
        if "stdout" in abridged_result and "stdout_lines" in abridged_result:
            #             abridged_result["stdout"] = """<omitted> use the following Ansible task to see the output:

            # - debug: msg={{ scriptOut.stdout }}
            #   tags: ['provisioner_wrapper']\n\n"""
            abridged_result["stdout_lines"] = "<omitted>"

        # if we already have stderr, we don't need stderr_lines
        if "stderr" in abridged_result and "stderr_lines" in abridged_result:
            abridged_result["stderr_lines"] = "<omitted>"

        if abridged_result:
            dumped += "\n"
            dumped += to_text(
                yaml.dump(abridged_result, allow_unicode=True, width=1000, Dumper=MyDumper, default_flow_style=False)
            )
            # For some reason, doesn't work when taking the escape logic to a method, haven't dug into it
            # ansi_escape = re.compile(r"(\[0)[0-?]*[ -\/]*[@-~]")
            # Clears the following color codes:
            # - '[0;32mINFO[0m'   (Shell)
            # - '[34m[1mDEBUG[0m' (Python)
            ansi_escape = re.compile(r"\[[0-9;]*m")
            dumped = ansi_escape.sub(repl="", string=dumped)

        # indent by a couple of spaces
        dumped = "\n  ".join(dumped.split("\n")).rstrip()
        return dumped

    def _serialize_diff(self, diff):
        return to_text(yaml.dump(diff, allow_unicode=True, width=1000, Dumper=AnsibleDumper, default_flow_style=False))
