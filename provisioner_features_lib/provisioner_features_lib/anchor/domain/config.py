#!/usr/bin/env python3

from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.shared.domain.config import GitHubConfig


class AnchorConfig(SerializationBase):
    """
    Configuration structure -

    anchor:
      github:
        organization: ZachiNachshon
        repository: provisioner
        branch: master
        git_access_token: SECRET
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "anchor" in dict_obj:
            self._parse_anchor_block(dict_obj["anchor"])
    
    def merge(self, other: "AnchorConfig") -> SerializationBase:
        if other.github.organization:
            self.github.organization = other.github.organization
        if other.github.repository:
            self.github.repository = other.github.repository
        if other.github.branch:
            self.github.branch = other.github.branch
        if other.github.git_access_token:
            self.github.git_access_token = other.github.git_access_token

        return self

    def _parse_anchor_block(self, anchor_block: dict):
        if "github" in anchor_block:
            github_block = anchor_block["github"]
            if "organization" in github_block:
                self.github.organization = github_block["organization"]
            if "repository" in github_block:
                self.github.repository = github_block["repository"]
            if "branch" in github_block:
                self.github.branch = github_block["branch"]
            if "git_access_token" in github_block:
                self.github.git_access_token = github_block["git_access_token"]

    github: GitHubConfig = None
