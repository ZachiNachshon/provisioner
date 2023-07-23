#!/usr/bin/env python3

from loguru import logger

from python_core_lib.infra.context import Context
from python_core_lib.utils.httpclient import HttpClient

GitHubUrl = "https://github.com"
GitHubApiUrl = "https://api.github.com"

GitHubApiLatestReleaseUrl = "{git_hub_api_url}/repos/{owner}/{repo}/releases/latest"
GitHubDownloadBinaryUrl = "{git_hub_url}/{owner}/{repo}/releases/download/{version}/{binary_name}"


class GitHub:

    _dry_run: bool = None
    _verbose: bool = None
    http_client: HttpClient = None

    def __init__(self, dry_run: bool, verbose: bool, http_client: HttpClient):
        self._dry_run = dry_run
        self._verbose = verbose
        self.http_client = http_client

    @staticmethod
    def create(ctx: Context, http_client: HttpClient) -> "GitHub":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating GitHub utility (dry_run: {dry_run}, verbose: {verbose})...")
        return GitHub(dry_run, verbose, http_client)

    def _get_latest_version(self, owner: str, repo: str) -> str:
        if self._dry_run:
            return "DRY_RUN_RESPONSE"

        version = None
        named_params = {
            "git_hub_api_url": GitHubApiUrl,
            "owner": owner,
            "repo": repo,
        }
        url = GitHubApiLatestReleaseUrl.format(**named_params)
        response = self.http_client.get_fn(url=url)
        if response.raw_res:
            json = response.raw_res.json()
            if "name" in json:
                version = json["name"]
            return version
        return version

    def _download_release_binary(
        self, owner: str, repo: str, version: str, binary_name: str, binary_folder_path: str
    ) -> str:
        named_params = {
            "git_hub_url": GitHubUrl,
            "owner": owner,
            "repo": repo,
            "version": version,
            "binary_name": binary_name,
        }
        url = GitHubDownloadBinaryUrl.format(**named_params)
        return self.http_client.download_file_fn(
            url=url, progress_bar=True, download_folder=binary_folder_path, verify_already_downloaded=True
        )

    get_latest_version_fn = _get_latest_version
    download_release_binary_fn = _download_release_binary
