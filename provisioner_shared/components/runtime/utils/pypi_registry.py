import json
from typing import Optional

from loguru import logger

from provisioner_shared.components.runtime.utils.httpclient import HttpClient


class PyPiRegistry:
    """Registry for PyPI package operations"""

    _http_client: HttpClient = None

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    @staticmethod
    def create(http_client: HttpClient) -> "PyPiRegistry":
        """Create a new PyPiRegistry instance"""
        logger.debug("Creating PyPI registry")
        return PyPiRegistry(http_client)

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """
        Get the latest version of a package from PyPI.

        Returns:
            Latest version string if found, None otherwise
        """
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            logger.debug(f"Fetching package info from PyPI: {url}")

            response_json = self._http_client.get_fn(url, timeout=10)
            data = json.loads(response_json)

            pypi_version = data.get("info", {}).get("version")
            if pypi_version:
                logger.debug(f"Found package version from PyPI: {pypi_version}")
                return pypi_version
            else:
                logger.debug("No version info found for package on PyPI")
                return None

        except Exception as e:
            logger.debug(f"Error fetching package version from PyPI: {e}")
            return None

    _get_package_version_fn = _get_package_version
