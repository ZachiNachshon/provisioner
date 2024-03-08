#!/usr/bin/env python3

from provisioner_features_lib.vcs.domain.config import VersionControlConfig
from provisioner_features_lib.vcs.typer_vcs_opts import TyperVersionControlOpts
from provisioner_features_lib.shared.domain.config import VersionControlConfig


class TestDataAnchorOpts:
    TEST_DATA_ANCHOR_GITHUB_ORGANIZATION = "test-organization"
    TEST_DATA_ANCHOR_GITHUB_REPOSITORY = "test-repository"
    TEST_DATA_ANCHOR_GITHUB_BRANCH = "test-branch"
    TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN = "test-access-token"

    @staticmethod
    def create_fake_anchor_opts() -> TyperVersionControlOpts:
        return TyperVersionControlOpts(
            vcs_config=VersionControlConfig(
                github=VersionControlConfig(
                    organization=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ORGANIZATION,
                    repository=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_REPOSITORY,
                    branch=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_BRANCH,
                    git_access_token=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN,
                )
            )
        )
