#!/usr/bin/env python3

from provisioner.domain.serialize import SerializationBase

"""
    Configuration structure -

    vcs:
      github:
        organization: ZachiNachshon
        repository: provisioner
        branch: master
        git_access_token: SECRET
    """

class GitHub(SerializationBase):
    organization: str = None
    repository: str = None
    branch: str = None
    git_access_token: str = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "GitHub") -> SerializationBase:
        if hasattr(other, "organization"):
            self.organization = other.organization
        if hasattr(other, "repository"):
            self.repository = other.repository
        if hasattr(other, "branch"):
            self.branch = other.branch
        if hasattr(other, "git_access_token"):
            self.git_access_token = other.git_access_token

        return self
    
    def _try_parse_config(self, dict_obj: dict) -> None:
        if "organization" in dict_obj:
            self.organization = dict_obj["organization"]
        if "repository" in dict_obj:
            self.repository = dict_obj["repository"]
        if "branch" in dict_obj:
            self.branch = dict_obj["branch"]
        if "git_access_token" in dict_obj:
            self.git_access_token = dict_obj["git_access_token"]

class VersionControlConfig(SerializationBase):
    github: GitHub = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "VersionControlConfig") -> SerializationBase:
        if hasattr(other, "github"):
            self.github.merge(other.github)
            
        return self
    
    def _try_parse_config(self, dict_obj: dict) -> None:
        if "github" in dict_obj:
            self.github = GitHub(dict_obj["github"])
