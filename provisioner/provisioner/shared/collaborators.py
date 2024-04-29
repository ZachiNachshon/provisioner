#!/usr/bin/env python3

import threading
from typing import Any, Callable

from provisioner.infra.context import Context
from provisioner.runner.ansible.ansible_runner import AnsibleRunnerLocal
from provisioner.utils.checks import Checks
from provisioner.utils.editor import Editor
from provisioner.utils.github import GitHub
from provisioner.utils.hosts_file import HostsFile
from provisioner.utils.httpclient import HttpClient
from provisioner.utils.io_utils import IOUtils
from provisioner.utils.json_util import JsonUtil
from provisioner.utils.network import NetworkUtil
from provisioner.utils.package_loader import PackageLoader
from provisioner.utils.paths import Paths
from provisioner.utils.printer import Printer
from provisioner.utils.process import Process
from provisioner.utils.progress_indicator import ProgressIndicator
from provisioner.utils.prompter import Prompter
from provisioner.utils.summary import Summary
from provisioner.utils.yaml_util import YamlUtil


class CoreCollaborators:
    def __init__(self, ctx: Context) -> None:
        self.__lock = threading.Lock()
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
        self.__yaml_util: YamlUtil = None

    # def run_in_sequence(*func):
    #     def compose(f, g):
    #         return lambda x : f(g(x))
    #     return reduce(compose, func, lambda x : x)

    def _lock_and_get(self, callback: Callable) -> Any:
        # TODO: Fix me, do not lock in here
        self.__lock = threading.Lock()
        with self.__lock:
            return callback()

    def io_utils(self) -> IOUtils:
        def create_io_utils():
            if not self.__io:
                self.__io = IOUtils.create(self.__ctx)
            return self.__io

        return self._lock_and_get(callback=create_io_utils)

    def paths(self) -> Paths:
        def create_paths():
            if not self.__paths:
                self.__paths = Paths.create(self.__ctx)
            return self.__paths

        return self._lock_and_get(callback=create_paths)

    def checks(self) -> Checks:
        def create_checks():
            if not self.__checks:
                self.__checks = Checks.create(self.__ctx)
            return self.__checks

        return self._lock_and_get(callback=create_checks)

    def json_util(self) -> JsonUtil:
        def create_json_util():
            if not self.__json_util:
                self.__json_util = JsonUtil.create(self.__ctx, self.io_utils())
            return self.__json_util

        return self._lock_and_get(callback=create_json_util)

    def process(self) -> Process:
        def create_process():
            if not self.__process:
                self.__process = Process.create(self.__ctx)
            return self.__process

        return self._lock_and_get(callback=create_process)

    def printer(self) -> Printer:
        def create_printer():
            if not self.__printer:
                self.__printer = Printer.create(self.__ctx)
            return self.__printer

        return self._lock_and_get(callback=create_printer)

    def prompter(self) -> Prompter:
        def create_prompter():
            if not self.__prompter:
                self.__prompter = Prompter.create(self.__ctx)
            return self.__prompter

        return self._lock_and_get(callback=create_prompter)

    def progress_indicator(self) -> ProgressIndicator:
        def create_progress_indicator():
            if not self.__progress_indicator:
                self.__progress_indicator = ProgressIndicator.create(self.__ctx, self.io_utils())
            return self.__progress_indicator

        return self._lock_and_get(callback=create_progress_indicator)

    def ansible_runner(self) -> AnsibleRunnerLocal:
        def create_ansible_runner():
            if not self.__ansible_runner:
                self.__ansible_runner = AnsibleRunnerLocal.create(self.__ctx, self.io_utils(), self.paths())
            return self.__ansible_runner

        return self._lock_and_get(callback=create_ansible_runner)

    def network_util(self) -> NetworkUtil:
        def create_network_util():
            if not self.__network_util:
                self.__network_util = NetworkUtil.create(self.__ctx, self.printer(), self.progress_indicator())
            return self.__network_util

        return self._lock_and_get(callback=create_network_util)

    def github(self) -> GitHub:
        def create_github():
            if not self.__github:
                self.__github = GitHub.create(self.__ctx, self.http_client())
            return self.__github

        return self._lock_and_get(callback=create_github)

    def summary(self) -> Summary:
        def create_summary():
            if not self.__summary:
                self.__summary = Summary.create(self.__ctx, self.json_util(), self.printer(), self.prompter())
            return self.__summary

        return self._lock_and_get(callback=create_summary)

    def hosts_file(self) -> HostsFile:
        def create_hosts_file():
            if not self.__hosts_file:
                self.__hosts_file = HostsFile.create(self.__ctx, self.process())
            return self.__hosts_file

        return self._lock_and_get(callback=create_hosts_file)

    def http_client(self) -> HttpClient:
        def create_http_client():
            if not self.__http_client:
                self.__http_client = HttpClient.create(
                    self.__ctx,
                    io_utils=self.io_utils(),
                    progress_indicator=self.progress_indicator(),
                    printer=self.printer(),
                )
            return self.__http_client

        return self._lock_and_get(callback=create_http_client)
    
    def editor(self) -> Editor:
        def create_editor():
            if not self.__editor:
                self.__editor = Editor.create(self.__ctx)
            return self.__editor

        return self._lock_and_get(callback=create_editor)

    def package_loader(self) -> PackageLoader:
        def create_package_loader():
            if not self.__package_loader:
                self.__package_loader = PackageLoader.create(self.__ctx)
            return self.__package_loader

        return self._lock_and_get(callback=create_package_loader)

    def yaml_util(self) -> YamlUtil:
        def create_yaml_util():
            if not self.__yaml_util:
                self.__yaml_util = YamlUtil.create(self.__ctx, self.io_utils())
            return self.__yaml_util

        return self._lock_and_get(callback=create_yaml_util)