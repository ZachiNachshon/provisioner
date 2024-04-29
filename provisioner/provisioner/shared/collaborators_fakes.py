#!/usr/bin/env python3

import threading
from typing import Any, Callable

from provisioner.infra.context import Context
from provisioner.runner.ansible.ansible_fakes import FakeAnsibleRunnerLocal
from provisioner.runner.ansible.ansible_runner import AnsibleRunnerLocal
from provisioner.shared.collaborators import CoreCollaborators
from provisioner.utils.checks import Checks
from provisioner.utils.checks_fakes import FakeChecks
from provisioner.utils.editor import Editor
from provisioner.utils.editor_fakes import FakeEditor
from provisioner.utils.github import GitHub
from provisioner.utils.github_fakes import FakeGitHub
from provisioner.utils.hosts_file import HostsFile
from provisioner.utils.hosts_file_fakes import FakeHostsFile
from provisioner.utils.httpclient import HttpClient
from provisioner.utils.httpclient_fakes import FakeHttpClient
from provisioner.utils.io_utils import IOUtils
from provisioner.utils.io_utils_fakes import FakeIOUtils
from provisioner.utils.json_util import JsonUtil
from provisioner.utils.network import NetworkUtil
from provisioner.utils.network_fakes import FakeNetworkUtil
from provisioner.utils.package_loader_fakes import FakePackageLoader
from provisioner.utils.paths import Paths
from provisioner.utils.paths_fakes import FakePaths
from provisioner.utils.printer import Printer
from provisioner.utils.printer_fakes import FakePrinter
from provisioner.utils.process import Process
from provisioner.utils.process_fakes import FakeProcess
from provisioner.utils.progress_indicator import ProgressIndicator
from provisioner.utils.progress_indicator_fakes import FakeProgressIndicator
from provisioner.utils.prompter import Prompter
from provisioner.utils.prompter_fakes import FakePrompter
from provisioner.utils.summary import Summary
from provisioner.utils.summary_fakes import FakeSummary


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
        self.__progress_indicator: ProgressIndicator = None
        self.__process: Process = None
        self.__ansible_runner: AnsibleRunnerLocal = None
        self.__network_util: NetworkUtil = None
        self.__github: GitHub = None
        self.__hosts_file: HostsFile = None
        self.__http_client: HttpClient = None
        self.__editor: Editor = None
        self.__package_loader: PackageLoader = None

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

    def override_io_utils(self, io_utils: IOUtils) -> None:
        self.__io = io_utils

    def paths(self) -> FakePaths:
        def create_paths():
            if not self.__paths:
                self.__paths = FakePaths.create(self.__ctx)
            return self.__paths

        return self._lock_and_get(callback=create_paths)

    def override_paths(self, paths: Paths) -> None:
        self.__paths = paths

    def checks(self) -> FakeChecks:
        def create_checks():
            if not self.__checks:
                self.__checks = FakeChecks.create(self.__ctx)
            return self.__checks

        return self._lock_and_get(callback=create_checks)

    def override_checks(self, checks: Checks) -> None:
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

    def override_process(self, process: Process) -> None:
        self.__process = process

    def printer(self) -> FakePrinter:
        def create_printer():
            if not self.__printer:
                self.__printer = FakePrinter.create(self.__ctx)
            return self.__printer

        return self._lock_and_get(callback=create_printer)

    def progress_indicator(self) -> FakeProgressIndicator:
        def create_progress_indicator():
            if not self.__progress_indicator:
                self.__progress_indicator = FakeProgressIndicator.create(self.__ctx)
            return self.__progress_indicator

        return self._lock_and_get(callback=create_progress_indicator)

    def override_printer(self, printer: Printer) -> None:
        self.__printer = printer

    def prompter(self) -> FakePrompter:
        def create_prompter():
            if not self.__prompter:
                self.__prompter = FakePrompter.create(self.__ctx)
            return self.__prompter

        return self._lock_and_get(callback=create_prompter)

    def override_prompter(self, prompter: Prompter) -> None:
        self.prompter = prompter

    def ansible_runner(self) -> FakeAnsibleRunnerLocal:
        def create_ansible_runner():
            if not self.__ansible_runner:
                self.__ansible_runner = FakeAnsibleRunnerLocal.create(self.__ctx)
            return self.__ansible_runner

        return self._lock_and_get(callback=create_ansible_runner)

    def override_ansible_runner(self, ansible_runner: AnsibleRunnerLocal) -> None:
        self.__ansible_runner = ansible_runner

    def network_util(self) -> FakeNetworkUtil:
        def create_network_util():
            if not self.__network_util:
                self.__network_util = FakeNetworkUtil.create(self.__ctx)
            return self.__network_util

        return self._lock_and_get(callback=create_network_util)

    def override_network_util(self, network_util: NetworkUtil) -> None:
        self.__network_util = network_util

    def github(self) -> FakeGitHub:
        def create_github():
            if not self.__github:
                self.__github = FakeGitHub.create(self.__ctx)
            return self.__github

        return self._lock_and_get(callback=create_github)

    def override_github(self, github: GitHub) -> None:
        self.__github = github

    def summary(self) -> FakeSummary:
        def create_summary():
            if not self.__summary:
                self.__summary = FakeSummary.create(self.__ctx)
            return self.__summary

        return self._lock_and_get(callback=create_summary)

    def override_summary(self, summary: Summary) -> None:
        self.__summary = summary

    def hosts_file(self) -> FakeHostsFile:
        def create_hosts_file():
            if not self.__hosts_file:
                self.__hosts_file = FakeHostsFile.create(self.__ctx)
            return self.__hosts_file

        return self._lock_and_get(callback=create_hosts_file)

    def override_hosts_file(self, hosts_file: HostsFile) -> None:
        self.__hosts_file = hosts_file

    def http_client(self) -> FakeHttpClient:
        def create_http_client():
            if not self.__http_client:
                self.__http_client = FakeHttpClient.create(self.__ctx)
            return self.__http_client

        return self._lock_and_get(callback=create_http_client)

    def override_http_client(self, http_client: HttpClient) -> None:
        self.__http_client = http_client

    def editor(self) -> FakeEditor:
        def create_editor():
            if not self.__editor:
                self.__editor = FakeEditor.create(self.__ctx)
            return self.__editor

        return self._lock_and_get(callback=create_editor)

    def override_editor(self, editor: FakeEditor) -> None:
        self.__editor = editor

    def package_loader(self) -> FakePackageLoader:
        def create_package_loader():
            if not self.__package_loader:
                self.__package_loader = FakePackageLoader.create(self.__ctx)
            return self.__package_loader

        return self._lock_and_get(callback=create_package_loader)

    def override_editor(self, package_loader: FakePackageLoader) -> None:
        self.__package_loader = package_loader
