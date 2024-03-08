#!/usr/bin/env python3

from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.shared.domain.config import VersionControlConfig


class VersionControlConfig(SerializationBase):
    """
    Configuration structure -

    vcs:
      github:
        organization: ZachiNachshon
        repository: provisioner
        branch: master
        git_access_token: SECRET
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "vcs" in dict_obj:
            self._parse_github_block(dict_obj["vcs"])
    
    def merge(self, other: "VersionControlConfig") -> SerializationBase:
        if other.github:
            self.github = other.github

        return self

    def _parse_github_block(self, vcs_block: dict):
        if "github" in vcs_block:
            self.github = VersionControlConfig.GitHub()
            github_block = vcs_block["github"]
            if "organization" in github_block:
                self.github.organization = github_block["organization"]
            if "repository" in github_block:
                self.github.repository = github_block["repository"]
            if "branch" in github_block:
                self.github.branch = github_block["branch"]
            if "git_access_token" in github_block:
                self.github.git_access_token = github_block["git_access_token"]

    class GitHub:
        organization: str = None
        repository: str = None
        branch: str = None
        git_access_token: str = None

        def __init__(self, organization: str = None, repository: str = None, branch: str = None, git_access_token: str = None) -> None:
            self.organization = organization
            self.repository = repository
            self.branch = branch
            self.git_access_token = git_access_token

    github: GitHub = None
