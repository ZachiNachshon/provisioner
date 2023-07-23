#!/usr/bin/env python3

import threading
from typing import Any, Callable

from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_fakes import FakeAnsibleRunnerLocal
from python_core_lib.runner.ansible.ansible_runner import AnsibleRunnerLocal
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.checks_fakes import FakeChecks
from python_core_lib.utils.github_fakes import FakeGitHub
from python_core_lib.utils.hosts_file import HostsFile
from python_core_lib.utils.hosts_file_fakes import FakeHostsFile
from python_core_lib.utils.httpclient import HttpClient
from python_core_lib.utils.httpclient_fakes import FakeHttpClient
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.io_utils_fakes import FakeIOUtils
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.network import NetworkUtil
from python_core_lib.utils.network_fakes import FakeNetworkUtil
from python_core_lib.utils.paths import Paths
from python_core_lib.utils.paths_fakes import FakePaths
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.printer_fakes import FakePrinter
from python_core_lib.utils.process import Process
from python_core_lib.utils.process_fakes import FakeProcess
from python_core_lib.utils.progress_indicator import ProgressIndicator
from python_core_lib.utils.prompter import Prompter
from python_core_lib.utils.prompter_fakes import FakePrompter
from python_core_lib.utils.summary import Summary
from python_core_lib.utils.summary_fakes import FakeSummary


class FakeCoreCollaborators(CoreCollaborators):
    def __init__(self, ctx: Context) -> None:
        # self.__lock = threading.Lock()
        self.__ctx: Context = ctx
        self.__io: IOUtils = None
        self.__paths: Paths = None
        self.__checks: Checks = None
        self.__json_util: JsonUtil = None
        self.__summary: Summary = None
        self.__prompter: Prompter = None
        self.__printer: Printer = None
        self.__process: Process = None
        self.__ansible_runner: AnsibleRunnerLocal = None
        self.__network_util: NetworkUtil = None
        self.__github: FakeGitHub = None
        self.__hosts_file: HostsFile = None
        self.__http_client: HttpClient = None

    def _lock_and_get(self, callback: Callable) -> Any:
        # TODO: Fix me, do not lock in here
        self.__lock = threading.Lock()
        with self.__lock:
            return callback()

    def io_utils(self) -> FakeIOUtils:
        def create_io_utils():
            if not self.__io:
                self.__io = FakeIOUtils.create(self.__ctx)
            return self.__io

        return self._lock_and_get(callback=create_io_utils)

    def override_io_utils(self, io_utils: FakeIOUtils) -> None:
        self.__io = io_utils

    def paths(self) -> FakePaths:
        def create_paths():
            if not self.__paths:
                self.__paths = FakePaths.create(self.__ctx)
            return self.__paths

        return self._lock_and_get(callback=create_paths)

    def override_paths(self, paths: FakePaths) -> None:
        self.__paths = paths

    def checks(self) -> FakeChecks:
        def create_checks():
            if not self.__checks:
                self.__checks = FakeChecks.create(self.__ctx)
            return self.__checks

        return self._lock_and_get(callback=create_checks)

    def override_checks(self, checks: FakeChecks) -> None:
        self.__checks = checks

    def json_util(self) -> JsonUtil:
        def create_json_util():
            if not self.__json_util:
                self.__json_util = JsonUtil.create(self.__ctx, self.io_utils())
            return self.__json_util

        return self._lock_and_get(callback=create_json_util)

    def override_json_util(self, json_util: JsonUtil) -> None:
        self.__json_util = json_util

    def process(self) -> FakeProcess:
        def create_process():
            if not self.__process:
                self.__process = FakeProcess.create(self.__ctx)
            return self.__process

        return self._lock_and_get(callback=create_process)

    def override_process(self, process: FakeProcess) -> None:
        self.__process = process

    def printer(self) -> FakePrinter:
        def create_printer():
            if not self.__printer:
                self.__printer = FakePrinter.create(self.__ctx, ProgressIndicator.create(self.__ctx, self.io_utils()))
            return self.__printer

        return self._lock_and_get(callback=create_printer)

    def override_printer(self, printer: FakePrinter) -> None:
        self.__printer = printer

    def prompter(self) -> FakePrompter:
        def create_prompter():
            if not self.__prompter:
                self.__prompter = FakePrompter.create(self.__ctx)
            return self.__prompter

        return self._lock_and_get(callback=create_prompter)

    def override_prompter(self, prompter: FakePrompter) -> None:
        self.prompter = prompter

    def ansible_runner(self) -> FakeAnsibleRunnerLocal:
        def create_ansible_runner():
            if not self.__ansible_runner:
                self.__ansible_runner = FakeAnsibleRunnerLocal.create(self.__ctx)
            return self.__ansible_runner

        return self._lock_and_get(callback=create_ansible_runner)

    def override_ansible_runner(self, ansible_runner: FakeAnsibleRunnerLocal) -> None:
        self.__ansible_runner = ansible_runner

    def network_util(self) -> FakeNetworkUtil:
        def create_network_util():
            if not self.__network_util:
                self.__network_util = FakeNetworkUtil.create(self.__ctx)
            return self.__network_util

        return self._lock_and_get(callback=create_network_util)

    def override_network_util(self, network_util: FakeNetworkUtil) -> None:
        self.__network_util = network_util

    def github(self) -> FakeGitHub:
        def create_github():
            if not self.__github:
                self.__github = FakeGitHub.create(self.__ctx)
            return self.__github

        return self._lock_and_get(callback=create_github)

    def override_github(self, github: FakeGitHub) -> None:
        self.__github = github

    def summary(self) -> FakeSummary:
        def create_summary():
            if not self.__summary:
                self.__summary = FakeSummary.create(self.__ctx)
            return self.__summary

        return self._lock_and_get(callback=create_summary)

    def override_summary(self, summary: FakeSummary) -> None:
        self.__summary = summary

    def hosts_file(self) -> FakeHostsFile:
        def create_hosts_file():
            if not self.__hosts_file:
                self.__hosts_file = FakeHostsFile.create(self.__ctx)
            return self.__hosts_file

        return self._lock_and_get(callback=create_hosts_file)

    def override_hosts_file(self, hosts_file: FakeHostsFile) -> None:
        self.__hosts_file = hosts_file

    def http_client(self) -> FakeHttpClient:
        def create_http_client():
            if not self.__http_client:
                self.__http_client = FakeHttpClient.create(self.__ctx, io_utils=self.io_utils(), printer=self.printer())
            return self.__http_client

        return self._lock_and_get(callback=create_http_client)

    def override_http_client(self, http_client: FakeHttpClient) -> None:
        self.__http_client = http_client
