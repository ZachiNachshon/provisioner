#!/usr/bin/env python3
"""
Package Deployer Script

This script handles package deployment operations including building, uploading to PyPI,
and managing GitHub releases for Poetry projects. It replaces the original bash script
with a more maintainable Python implementation.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# ANSI color codes for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    LIGHT_CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NONE = "\033[0m"


@dataclass
class CliArguments:
    """Container for parsed CLI arguments."""

    command: str
    build_type: Optional[str] = None
    version: Optional[str] = None
    multi_project: bool = False
    compress: Optional[str] = None
    project_path: Optional[str] = None
    output_path: Optional[str] = None
    upload_action: Optional[str] = None
    source_tag: Optional[str] = None
    release_tag: Optional[str] = None
    release_title: Optional[str] = None
    release_notes_file: Optional[str] = None
    assets_dir: Optional[str] = None
    target_branch: Optional[str] = None
    auto_prompt: bool = False


@dataclass
class PackageInfo:
    """Container for package information."""

    name: str
    version: str
    custom_version: Optional[str] = None

    @property
    def effective_version(self) -> str:
        """Get the effective version (custom if set, otherwise current)."""
        return self.custom_version or self.version

    @property
    def escaped_name(self) -> str:
        """Get package name with underscores for file naming."""
        return self.name.replace("-", "_")


class Logger:
    """Handles logging with colored output."""

    @staticmethod
    def debug(message: str) -> None:
        """Log debug message."""
        print(f"{Colors.WHITE}DEBUG{Colors.NONE}: {message}")

    @staticmethod
    def info(message: str) -> None:
        """Log info message."""
        print(f"{Colors.GREEN}INFO{Colors.NONE}: {message}")

    @staticmethod
    def warning(message: str) -> None:
        """Log warning message."""
        print(f"{Colors.YELLOW}WARNING{Colors.NONE}: {message}")

    @staticmethod
    def error(message: str) -> None:
        """Log error message."""
        print(f"{Colors.RED}ERROR{Colors.NONE}: {message}")

    @staticmethod
    def fatal(message: str) -> None:
        """Log fatal error and exit."""
        print(f"{Colors.RED}ERROR{Colors.NONE}: {message}")
        sys.exit(1)


class CommandRunner:
    """Handles running system commands."""

    @staticmethod
    def run_command(command: str, cwd: Optional[Path] = None, capture_output: bool = True) -> str:
        """
        Run a system command and return output.

        Args:
            command: Command to run
            cwd: Working directory
            capture_output: Whether to capture output

        Returns:
            Command output as string

        Raises:
            RuntimeError: If command fails
        """
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(cwd) if cwd else None, capture_output=capture_output, text=True, check=True
            )
            return result.stdout.strip() if capture_output else ""
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {command}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            raise RuntimeError(error_msg)

    @staticmethod
    def check_tool_exists(tool_name: str) -> None:
        """
        Check if a required tool exists in PATH.

        Args:
            tool_name: Name of the tool to check

        Raises:
            RuntimeError: If tool is not found
        """
        try:
            subprocess.run(["which", tool_name], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            Logger.fatal(f"Required tool not found: {tool_name}")


class Prompter:
    """Handles user prompts and confirmations."""

    def __init__(self, auto_prompt: bool = False):
        self.auto_prompt = auto_prompt

    def prompt_yes_no(self, message: str, level: str = "normal") -> bool:
        """
        Prompt user for yes/no confirmation.

        Args:
            message: Prompt message
            level: Severity level (normal, warning, critical)

        Returns:
            True if user confirms, False otherwise
        """
        if self.auto_prompt:
            print(f"{self._get_colored_prompt(message, level)}y\n")
            return True

        response = input(self._get_colored_prompt(message, level))
        return response.lower() == "y"

    def _get_colored_prompt(self, message: str, level: str) -> str:
        """Get colored prompt based on level."""
        if level == "critical":
            return f"{Colors.RED}{message}? (y/n):{Colors.NONE} "
        elif level == "warning":
            return f"{Colors.YELLOW}{message}? (y/n):{Colors.NONE} "
        else:
            return f"{message}? (y/n): "


class FileManager:
    """Handles file operations and compression."""

    @staticmethod
    def create_temp_directory(prefix: str) -> Path:
        """Create a temporary directory."""
        return Path(tempfile.mkdtemp(prefix=prefix))

    @staticmethod
    def compress_file_to_tar_gz(source_file: Path, output_path: Path, new_name: str) -> Path:
        """
        Compress a file to tar.gz format with a new name.

        Args:
            source_file: Source file to compress
            output_path: Output directory
            new_name: New name for the compressed file

        Returns:
            Path to the compressed file
        """
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        output_path.mkdir(parents=True, exist_ok=True)
        compressed_file = output_path / new_name

        with tarfile.open(compressed_file, "w:gz") as tar:
            tar.add(source_file, arcname=source_file.name)

        Logger.info(f"Compressed file created: {compressed_file}")
        return compressed_file

    @staticmethod
    def extract_tar_gz(tar_file: Path, extract_dir: Path) -> List[Path]:
        """
        Extract tar.gz file and return list of extracted files.

        Args:
            tar_file: Path to tar.gz file
            extract_dir: Directory to extract to

        Returns:
            List of extracted file paths
        """
        extract_dir.mkdir(parents=True, exist_ok=True)
        extracted_files = []

        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(extract_dir)
            extracted_files = [extract_dir / member.name for member in tar.getmembers()]

        return extracted_files


class PoetryManager:
    """Handles Poetry operations."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.command_runner = CommandRunner()

    def get_package_info(self) -> PackageInfo:
        """
        Get package name and version from Poetry.

        Returns:
            PackageInfo object with name and version
        """
        if not (self.project_path / "pyproject.toml").exists():
            Logger.fatal(f"pyproject.toml not found in {self.project_path}")

        version_output = self.command_runner.run_command("poetry version --no-ansi", cwd=self.project_path)

        # Parse "package-name x.y.z" format
        parts = version_output.split()
        if len(parts) < 2:
            Logger.fatal("Could not parse poetry version output")

        package_name = " ".join(parts[:-1])
        version = parts[-1]

        if not package_name.strip() or not version.strip():
            Logger.fatal("Could not resolve package name or version")

        Logger.info(f"Identified package: {package_name}, version: {version}")
        return PackageInfo(name=package_name, version=version)

    def update_version(self, new_version: str) -> None:
        """Update package version using Poetry."""
        Logger.info(f"Updating poetry version to: {new_version}")
        self.command_runner.run_command(f"poetry version {new_version}", cwd=self.project_path)

    def update_lock_file(self) -> None:
        """Update Poetry lock file."""
        Logger.info("Updating Poetry lock file")
        self.command_runner.run_command("poetry lock", cwd=self.project_path)

    def build_package(self, build_type: str, multi_project: bool = False) -> Path:
        """
        Build package using Poetry.

        Args:
            build_type: Either 'sdist' or 'wheel'
            multi_project: Whether to use multi-project build

        Returns:
            Path to the built package file
        """
        if build_type not in ["sdist", "wheel"]:
            Logger.fatal(f"Invalid build type: {build_type}. Must be 'sdist' or 'wheel'")

        project_type = "BUNDLED MULTI PROJECT" if multi_project else "NON-BUNDLED SINGLE PROJECT"
        Logger.info(f"Building {build_type} - {Colors.YELLOW}{project_type}{Colors.NONE}")

        build_command = self._get_build_command(build_type, multi_project)
        self.command_runner.run_command(build_command, cwd=self.project_path)

        return self._find_built_package(build_type)

    def _get_build_command(self, build_type: str, multi_project: bool) -> str:
        """Get the appropriate Poetry build command."""
        if multi_project:
            # return f"poetry build-project -f {build_type} -vv"
            return f"poetry build -f {build_type} -vv"
        else:
            return f"poetry build -f {build_type} -vv"

    def _find_built_package(self, build_type: str) -> Path:
        """Find the built package file in the dist directory."""
        dist_dir = self.project_path / "dist"
        if not dist_dir.exists():
            Logger.fatal("dist directory not found after build")

        extension = ".tar.gz" if build_type == "sdist" else ".whl"
        package_files = list(dist_dir.glob(f"*{extension}"))

        if not package_files:
            Logger.fatal(f"No {build_type} package found in dist directory")

        # Return the most recently created file
        return max(package_files, key=lambda p: p.stat().st_mtime)


class ManifestManager:
    """Handles manifest.json updates."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.manifest_path = project_path / "resources" / "manifest.json"

    def update_version(self, version: str) -> None:
        """Update version in manifest.json if it exists."""
        if not self.manifest_path.exists():
            Logger.warning(f"manifest.json not found at {self.manifest_path}")
            return

        Logger.info(f"Updating manifest.json version to: {version}")

        try:
            with open(self.manifest_path, "r") as f:
                manifest_data = json.load(f)

            manifest_data["version"] = version

            with open(self.manifest_path, "w") as f:
                json.dump(manifest_data, f, indent=2)

        except Exception as e:
            Logger.error(f"Failed to update manifest.json: {e}")


class GitHubReleaseManager:
    """Handles GitHub release operations."""

    def __init__(self):
        self.command_runner = CommandRunner()
        self._validate_github_token()

    def _validate_github_token(self) -> None:
        """Validate that GITHUB_TOKEN is available."""
        if not os.environ.get("GITHUB_TOKEN"):
            Logger.fatal("GITHUB_TOKEN environment variable is required")

    def check_release_exists(self, tag: str) -> bool:
        """Check if a GitHub release exists for the given tag."""
        try:
            self.command_runner.run_command(f'gh release view "{tag}" > /dev/null 2>&1')
            return True
        except RuntimeError:
            return False

    def create_release(
        self,
        tag: str,
        title: str,
        notes_file: Optional[Path] = None,
        is_prerelease: bool = False,
        target_branch: str = "master",
    ) -> None:
        """
        Create a new GitHub release.

        Args:
            tag: Release tag
            title: Release title
            notes_file: Path to release notes file
            is_prerelease: Whether this is a pre-release
            target_branch: Target branch for the release
        """
        if self.check_release_exists(tag):
            Logger.fatal(f"Release {tag} already exists")

        command_parts = [f'gh release create "{tag}"', f'--title "{title}"']

        if notes_file and notes_file.exists():
            command_parts.append(f'--notes-file "{notes_file}"')

        if is_prerelease:
            command_parts.append("--prerelease")

        if target_branch:
            command_parts.append(f'--target "{target_branch}"')

        command = " ".join(command_parts)
        Logger.info(f"Creating GitHub release: {tag}, prerelease: {is_prerelease}")

        self.command_runner.run_command(command)

    def upload_assets(self, tag: str, assets: List[Path]) -> None:
        """Upload assets to a GitHub release."""
        if not assets:
            Logger.warning("No assets to upload")
            return

        assets_str = " ".join(f'"{asset}"' for asset in assets)
        command = f'gh release upload "{tag}" {assets_str}'

        Logger.info(f"Uploading {len(assets)} assets to release {tag}")
        self.command_runner.run_command(command)

    def upload_assets_from_directory(self, tag: str, assets_dir: Path) -> None:
        """Upload all assets from a directory to a GitHub release."""
        if not assets_dir.exists() or not assets_dir.is_dir():
            Logger.warning(f"Assets directory not found: {assets_dir}")
            return

        assets = list(assets_dir.iterdir())
        if not assets:
            Logger.warning(f"No assets found in directory: {assets_dir}")
            return

        self.upload_assets(tag, assets)

    def download_release_assets(self, source_tag: str, download_dir: Path) -> List[Path]:
        """
        Download all assets from a GitHub release.

        Args:
            source_tag: Source release tag
            download_dir: Directory to download assets to

        Returns:
            List of downloaded asset paths
        """
        if not self.check_release_exists(source_tag):
            Logger.fatal(f"GitHub release not found: {source_tag}")

        download_dir.mkdir(parents=True, exist_ok=True)

        Logger.info(f"Downloading assets from GitHub release: {source_tag}")

        try:
            self.command_runner.run_command(f'gh release download "{source_tag}" --dir "{download_dir}"')
        except RuntimeError as e:
            Logger.warning(f"Download failed: {e}")
            return []

        assets = list(download_dir.iterdir())
        Logger.info(f"Downloaded {len(assets)} assets to: {download_dir}")

        if not assets:
            Logger.warning(f"No assets found in release {source_tag}")

        return assets


class PyPIUploader:
    """Handles PyPI upload operations."""

    def __init__(self):
        self._validate_pypi_token()

    def _validate_pypi_token(self) -> None:
        """Validate that PYPI_API_TOKEN is available."""
        if not os.environ.get("PYPI_API_TOKEN"):
            Logger.fatal("PYPI_API_TOKEN environment variable is required")

    def upload_package(self, package_file: Path) -> None:
        """
        Upload a package to PyPI.

        Args:
            package_file: Path to the package file to upload
        """
        if not package_file.exists():
            Logger.fatal(f"Package file not found: {package_file}")

        username = "__token__"
        password = os.environ["PYPI_API_TOKEN"]

        Logger.info(f"Uploading package to PyPI: {package_file.name}")

        try:
            command = f'twine upload --username "{username}" --password "{password}" "{package_file}"'
            CommandRunner.run_command(command)
            Logger.info(f"Successfully uploaded {package_file.name} to PyPI")
        except RuntimeError as e:
            Logger.fatal(f"Failed to upload package to PyPI: {e}")


class PackageDeployer:
    """Main package deployment orchestrator."""

    def __init__(self, args: CliArguments):
        self.args = args
        self.prompter = Prompter(args.auto_prompt)
        self.project_path = Path(args.project_path or ".")

        # Initialize managers (lazy-loaded as needed)
        self.poetry_manager = PoetryManager(self.project_path)
        self.manifest_manager = ManifestManager(self.project_path)
        self._github_manager: Optional[GitHubReleaseManager] = None
        self._pypi_uploader: Optional[PyPIUploader] = None

        # Package info will be set during execution
        self.package_info: Optional[PackageInfo] = None
        self.built_package_path: Optional[Path] = None

    @property
    def github_manager(self) -> GitHubReleaseManager:
        """Lazy-load GitHub manager only when needed."""
        if self._github_manager is None:
            self._github_manager = GitHubReleaseManager()
        return self._github_manager

    @property
    def pypi_uploader(self) -> PyPIUploader:
        """Lazy-load PyPI uploader only when needed."""
        if self._pypi_uploader is None:
            self._pypi_uploader = PyPIUploader()
        return self._pypi_uploader

    def execute_command(self) -> None:
        """Execute the specified command."""
        # Check prerequisites
        self._check_prerequisites()

        # Initialize project
        self._initialize_project()

        # Execute the appropriate command
        command_handlers = {
            "build": self._handle_build_command,
            "upload": self._handle_upload_command,
            "prerelease": self._handle_prerelease_command,
        }

        handler = command_handlers.get(self.args.command)
        if not handler:
            Logger.fatal(f"Unknown command: {self.args.command}")
            return  # Added return to prevent calling None handler in tests

        handler()

    def _check_prerequisites(self) -> None:
        """Check that all required tools are available."""
        CommandRunner.check_tool_exists("poetry")

        if self.args.version:
            CommandRunner.check_tool_exists("jq")

        if self.args.command in ["upload", "prerelease"]:
            CommandRunner.check_tool_exists("gh")

        if self.args.command == "upload" and self.args.upload_action == "upload-to-pypi":
            CommandRunner.check_tool_exists("twine")

    def _initialize_project(self) -> None:
        """Initialize project context."""
        # Change to project directory if specified
        if self.args.project_path:
            self._change_to_project_directory()

        # Reinitialize managers after directory change
        self.poetry_manager = PoetryManager(self.project_path)
        self.manifest_manager = ManifestManager(self.project_path)

        # Update lock file
        self.poetry_manager.update_lock_file()

        # Get package information
        self.package_info = self.poetry_manager.get_package_info()

        # Apply custom version if specified
        if self.args.version:
            self._apply_custom_version()

    def _change_to_project_directory(self) -> None:
        """Change to the specified project directory."""
        project_path = Path(self.args.project_path)

        if not project_path.exists():
            Logger.fatal(f"Project path does not exist: {project_path}")

        if not project_path.is_dir():
            Logger.fatal(f"Project path is not a directory: {project_path}")

        # Resolve output path to absolute if needed
        if self.args.output_path and not Path(self.args.output_path).is_absolute():
            self.args.output_path = str(Path(self.args.output_path).resolve())

        Logger.info(f"Changing to project directory: {project_path}")
        try:
            os.chdir(project_path)
            self.project_path = Path(os.getcwd())  # Use current working directory
        except (FileNotFoundError, NotADirectoryError) as e:
            Logger.fatal(f"Failed to change to directory {project_path}: {e}")

    def _apply_custom_version(self) -> None:
        """Apply custom version if specified."""
        if not self.args.version:
            return

        Logger.info(f"Applying custom version: {self.args.version}")

        # Update package info
        self.package_info.custom_version = self.args.version

        # Update poetry version
        self.poetry_manager.update_version(self.args.version)

        # Update manifest version
        self.manifest_manager.update_version(self.args.version)

        Logger.info(f"Version updated successfully to: {self.args.version}")

    def _handle_build_command(self) -> None:
        """Handle the build command."""
        Logger.info("Building package...")

        # Build the package
        self.built_package_path = self.poetry_manager.build_package(self.args.build_type, self.args.multi_project)

        # Handle compression if requested
        final_output_path = self._handle_compression_if_needed()

        Logger.info(f"Build completed. Output: {final_output_path}")

    def _handle_compression_if_needed(self) -> Path:
        """Handle package compression if needed."""
        if not self.args.compress == "tar.gz":
            return self.built_package_path

        # Determine output directory
        if self.args.output_path:
            output_dir = Path(self.args.output_path)
        else:
            output_dir = self.built_package_path.parent

        # Create compressed filename
        effective_version = self.package_info.effective_version
        compressed_name = f"{self.package_info.name}-v{effective_version}.tar.gz"

        # Compress the file
        compressed_path = FileManager.compress_file_to_tar_gz(self.built_package_path, output_dir, compressed_name)

        return compressed_path

    def _handle_upload_command(self) -> None:
        """Handle the upload command."""
        Logger.info("Processing upload command...")

        if self.args.upload_action == "promote-rc":
            self._promote_rc_to_ga()
        elif self.args.upload_action == "upload-to-pypi":
            self._upload_ga_to_pypi()
        else:
            Logger.fatal(f"Invalid upload action: {self.args.upload_action}")

    def _promote_rc_to_ga(self) -> None:
        """Promote RC release to GA."""
        source_tag = self.args.source_tag
        target_tag = self.args.release_tag
        target_title = self.args.release_title or f"Release {target_tag}"

        Logger.info(f"Promoting RC to GA: {source_tag} -> {target_tag}")

        # Download RC assets
        temp_dir = FileManager.create_temp_directory("rc-assets-")
        try:
            assets = self.github_manager.download_release_assets(source_tag, temp_dir)

            if not assets:
                Logger.fatal(f"No assets found in RC release {source_tag}")

            Logger.info(f"Found {len(assets)} assets in RC release")

            # Create GA release
            notes_file = Path(self.args.release_notes_file) if self.args.release_notes_file else None
            self.github_manager.create_release(target_tag, target_title, notes_file, is_prerelease=False)

            # Upload assets to GA release
            self.github_manager.upload_assets(target_tag, assets)

            Logger.info(f"Successfully promoted RC to GA: {source_tag} -> {target_tag}")

        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _upload_ga_to_pypi(self) -> None:
        """Upload GA release to PyPI."""
        source_tag = self.args.source_tag

        Logger.info(f"Uploading GA release to PyPI: {source_tag}")

        # Download GA release assets
        temp_dir = FileManager.create_temp_directory("ga-assets-")
        try:
            assets = self.github_manager.download_release_assets(source_tag, temp_dir)

            # Find compressed asset for this package
            package_name = self.package_info.name
            compressed_asset = None

            for asset in assets:
                if asset.name.startswith(f"{package_name}-v") and asset.name.endswith(".tar.gz"):
                    compressed_asset = asset
                    break

            if not compressed_asset:
                Logger.fatal(f"Compressed asset not found for {package_name}")

            Logger.info(f"Found compressed asset: {compressed_asset.name}")

            # Extract the compressed asset
            extract_dir = FileManager.create_temp_directory("extracted-")
            try:
                extracted_files = FileManager.extract_tar_gz(compressed_asset, extract_dir)

                # Find wheel file
                wheel_file = None
                for file_path in extracted_files:
                    if file_path.suffix == ".whl":
                        wheel_file = file_path
                        break

                if not wheel_file:
                    Logger.fatal("Wheel file not found in compressed asset")

                Logger.info(f"Extracted wheel file: {wheel_file.name}")

                # Upload to PyPI
                self.pypi_uploader.upload_package(wheel_file)

                Logger.info(f"Successfully uploaded {package_name} to PyPI")

            finally:
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _handle_prerelease_command(self) -> None:
        """Handle the prerelease command."""
        Logger.info("Creating GitHub pre-release...")

        release_tag = self.args.release_tag
        release_title = self.args.release_title or f"Release Candidate {release_tag}"
        target_branch = self.args.target_branch or "master"

        # Resolve assets directory to absolute path if needed
        assets_dir = None
        if self.args.assets_dir:
            assets_dir = Path(self.args.assets_dir)
            if not assets_dir.is_absolute():
                assets_dir = assets_dir.resolve()
            Logger.info(f"Resolved assets directory: {assets_dir}")

        # Create pre-release
        notes_file = Path(self.args.release_notes_file) if self.args.release_notes_file else None
        self.github_manager.create_release(
            release_tag, release_title, notes_file, is_prerelease=True, target_branch=target_branch
        )

        # Upload assets if provided
        if assets_dir:
            self.github_manager.upload_assets_from_directory(release_tag, assets_dir)

        Logger.info(f"Pre-release created successfully: {release_tag}")


class PackageDeployerCLI:
    """Handles CLI operations for PackageDeployer."""

    SCRIPT_TITLE = "Poetry Package Deployer"

    def run(self) -> None:
        """Main entry point for CLI execution."""
        try:
            args = self._parse_arguments()
            deployer = PackageDeployer(args)
            deployer.execute_command()
        except Exception as e:
            Logger.fatal(str(e))

    def _parse_arguments(self) -> CliArguments:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description=f"{self.SCRIPT_TITLE} - Build and release pip packages from Poetry projects",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_help_epilog(),
        )

        # Commands (subparsers)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Helper function to add global arguments to each subparser
        def add_global_arguments(subparser):
            subparser.add_argument("--project-path", help="Path to project directory (default: current directory)")
            subparser.add_argument(
                "-y", "--auto-prompt", action="store_true", help="Do not prompt for approval and accept everything"
            )

        # Build command
        build_parser = subparsers.add_parser("build", help="Build pip package (sdist/wheel) to dist folder")
        build_parser.add_argument(
            "--build-type", required=True, choices=["sdist", "wheel"], help="Package build type [options: sdist/wheel]"
        )
        build_parser.add_argument("--version", help="Custom version to build (default: current poetry version)")
        build_parser.add_argument("--compress", choices=["tar.gz"], help="Release asset format [options: tar.gz]")
        build_parser.add_argument("--output-path", help="Output directory for compressed assets (default: dist)")
        build_parser.add_argument(
            "--multi-project", action="store_true", help="Use multi-project build mode (bundled projects)"
        )
        add_global_arguments(build_parser)

        # Upload command
        upload_parser = subparsers.add_parser(
            "upload", help="Download GitHub release and promote RC to GA or upload GA to PyPI"
        )
        upload_parser.add_argument(
            "--upload-action",
            required=True,
            choices=["promote-rc", "upload-to-pypi"],
            help="Upload action [options: promote-rc/upload-to-pypi]",
        )
        upload_parser.add_argument(
            "--source-tag", required=True, help="Source GitHub release tag to download (example: v1.0.0-RC.1)"
        )
        upload_parser.add_argument("--release-tag", help="Target release tag for promote-rc action (example: v1.0.0)")
        upload_parser.add_argument("--release-title", help="Target release title for promote-rc action")
        upload_parser.add_argument("--release-notes-file", help="Path to release notes file")
        add_global_arguments(upload_parser)

        # Prerelease command
        prerelease_parser = subparsers.add_parser("prerelease", help="Create GitHub pre-release with assets")
        prerelease_parser.add_argument("--release-tag", required=True, help="GitHub release tag (example: v1.0.0-RC.1)")
        prerelease_parser.add_argument("--release-title", help="GitHub release title")
        prerelease_parser.add_argument("--release-notes-file", help="Path to release notes file")
        prerelease_parser.add_argument("--assets-dir", help="Directory containing assets to upload")
        prerelease_parser.add_argument(
            "--target-branch", default="master", help="Target branch for release (default: master)"
        )
        add_global_arguments(prerelease_parser)

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            sys.exit(1)

        # Additional validation
        self._validate_arguments(args)

        return self._convert_to_cli_arguments(args)

    def _validate_arguments(self, args) -> None:
        """Validate parsed arguments."""
        # Upload action validation
        if args.command == "upload":
            if args.upload_action == "promote-rc" and not args.release_tag:
                Logger.fatal("promote-rc action requires --release-tag")

        # Note: Environment variable validation is moved to when managers are actually used
        # This matches the bash script behavior where tokens are only checked when needed

    def _convert_to_cli_arguments(self, args) -> CliArguments:
        """Convert argparse Namespace to CliArguments."""
        return CliArguments(
            command=args.command,
            build_type=getattr(args, "build_type", None),
            version=getattr(args, "version", None),
            multi_project=getattr(args, "multi_project", False),
            compress=getattr(args, "compress", None),
            project_path=getattr(args, "project_path", None),
            output_path=getattr(args, "output_path", None),
            upload_action=getattr(args, "upload_action", None),
            source_tag=getattr(args, "source_tag", None),
            release_tag=getattr(args, "release_tag", None),
            release_title=getattr(args, "release_title", None),
            release_notes_file=getattr(args, "release_notes_file", None),
            assets_dir=getattr(args, "assets_dir", None),
            target_branch=getattr(args, "target_branch", None),
            auto_prompt=getattr(args, "auto_prompt", False),
        )

    def _get_help_epilog(self) -> str:
        """Get help epilog text."""
        return """
VERSIONING PRINCIPLE ("Build Once, Promote Many"):
  --version flag:     Package version (stable, e.g., 1.2.3) - stamped in packages
  --release-tag:      Git/GitHub tag (with RC suffix, e.g., v1.2.3-RC.1)
  
  RC packages contain STABLE version 1.2.3, tagged as v1.2.3-RC.1
  GA promotion reuses same packages, creates new tag v1.2.3

EXAMPLES:
  Build with final version for RC:
    python package_deployer.py build --build-type wheel --version 1.2.3 --compress tar.gz

  Create RC release (packages have v1.2.3, release tagged v1.2.3-RC.1):
    python package_deployer.py prerelease --release-tag v1.2.3-RC.1 --assets-dir ./assets

  Promote RC to GA (reuse v1.2.3 packages, new tag v1.2.3):
    python package_deployer.py upload --upload-action promote-rc --source-tag v1.2.3-RC.1 --release-tag v1.2.3

  Upload to PyPI (uploads packages with v1.2.3):
    python package_deployer.py upload --upload-action upload-to-pypi --source-tag v1.2.3

  Multi-project build:
    python package_deployer.py build --build-type wheel --version 1.2.3 --project-path provisioner --output-path ./dist

ENVIRONMENT VARIABLES:
  GITHUB_TOKEN    - Required for GitHub operations (gh CLI)
  PYPI_API_TOKEN  - Required for PyPI uploads (twine)

NOTES:
  - Use -y for non-interactive mode (CI/CD)
  - Use absolute paths for --assets-dir with --project-path
  - Plugin tags: examples-plugin-v1.2.3-RC.1 (auto-generated)
        """


def main():
    """Main function."""
    cli = PackageDeployerCLI()
    cli.run()


if __name__ == "__main__":
    main()
