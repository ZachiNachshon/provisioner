#!/usr/bin/env python3


class VersionControlConfig:

    organization: str = None
    repository: str = None
    branch: str = None
    git_access_token: str = None

    def __init__(
        self, organization: str = None, repository: str = None, branch: str = None, git_access_token: str = None
    ) -> None:
        self.organization = organization
        self.repository = repository
        self.branch = branch
        self.git_access_token = git_access_token
