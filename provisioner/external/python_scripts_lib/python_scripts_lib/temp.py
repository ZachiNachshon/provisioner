#!/usr/bin/env python3

import re
from abc import abstractmethod
from time import sleep

from python_scripts_lib.infra.context import Context
from python_scripts_lib.utils.hosts_file import HostsFile
from python_scripts_lib.utils.httpclient import HttpClient
from python_scripts_lib.utils.io_utils import IOUtils
from python_scripts_lib.utils.network import NetworkUtil
from python_scripts_lib.utils.process import Process
from python_scripts_lib.utils.progress_indicator import ProgressIndicator

# ctx = Context.create()
# process = Process.create(ctx)
# hosts_file = HostsFile.create(ctx, process)
# hosts_file.add_entry_fn(ip_address="1.1.1.2", dns_names=["zachi2.test.com"], comment="This is a test")


# url="https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2022-01-28/2022-01-28-raspios-bullseye-arm64-lite.zip",
# ctx = Context.create()
# client = HttpClient.create(ctx, IOUtils(ctx))
# output = client.download_file_fn(
#     url="http://212.183.159.230/50MB.zip", download_folder="/Users/zachin/temp/rpi_raspios_image", progress_bar=True
# )

# print(output)

# network = NetworkUtil.create(ctx, pb)
# result = network.get_all_lan_network_devices_fn(ip_range="192.168.1.1/24")
# print(result)


def _escape_ansi(line: str) -> str:
    # ansi_escape = re.compile(
    #     '(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])'
    # )
    # ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]', flags=re.IGNORECASE)
    # ansi_escape = re.compile(r'''(\[([01];)?\d+m){1,}(?=\[[A-Z]+\])''')
    ansi_escape = re.compile(r"(\[0)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub(repl="", string=line)
    # return re.sub('\033\\[([0-9]+)(;[0-9]+)*m', '', line)


before = """
WARNING: Supported ansible-playbook version is 2.11.7
INFO: Running within a Docker container. name: ansible-playbook


PLAY [Hello World Run] *********************************************************

TASK [../../../external/ansible_playbooks/playbooks/roles/hello_world : Define shell_scripts_lib files] ***
ok: [localhost]

TASK [Copy shell_scripts_lib files] ********************************************

TASK [../../../external/ansible_playbooks/playbooks/roles/shell_scripts_lib : Creates directory] ***
changed: [localhost]

TASK [../../../external/ansible_playbooks/playbooks/roles/shell_scripts_lib : Copy shell_scripts_lib selected files] ***
changed: [localhost] => (item=logger.sh)
changed: [localhost] => (item=cmd.sh)

TASK [../../../external/ansible_playbooks/playbooks/roles/hello_world : Print a greeting to stdout] ***
ok: [localhost]

TASK [../../../external/ansible_playbooks/playbooks/roles/hello_world : debug] ***
ok: [localhost] => 
  msg: |-
    [0;32mINFO (Dry Run)[0m: Dry run: enabled
    [0;32mINFO (Dry Run)[0m: Verbose: enabled
  
        Hello World, John Doe !

PLAY RECAP *********************************************************************
localhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
"""

print("BEFORE: " + before)

after = _escape_ansi(before)

print("AFTER: " + after)
