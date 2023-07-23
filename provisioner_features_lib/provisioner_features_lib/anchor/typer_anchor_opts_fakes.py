#!/usr/bin/env python3

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.shared.domain.config import GitHubConfig


class TestDataAnchorOpts:
    TEST_DATA_ANCHOR_GITHUB_ORGANIZATION = "test-organization"
    TEST_DATA_ANCHOR_GITHUB_REPOSITORY = "test-repository"
    TEST_DATA_ANCHOR_GITHUB_BRANCH = "test-branch"
    TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN = "test-access-token"

    @staticmethod
    def create_fake_anchor_opts() -> TyperAnchorOpts:
        return TyperAnchorOpts(
            anchor_config=AnchorConfig(
                github=GitHubConfig(
                    organization=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ORGANIZATION,
                    repository=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_REPOSITORY,
                    branch=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_BRANCH,
                    git_access_token=TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ACCESS_TOKEN,
                )
            )
        )
