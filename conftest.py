# import docker
import os
import subprocess

import pytest

# Configure Docker logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('docker')
# logger.setLevel(logging.DEBUG)


# Register pytest command-line options
def pytest_addoption(parser):
    parser.addoption("--all", action="store_true", default=False, help="Run all tests (unit, integration, and E2E)")
    parser.addoption("--only-e2e", action="store_true", default=False, help="Run only E2E tests")
    parser.addoption(
        "--skip-e2e", action="store_true", default=False, help="Skip E2E tests and run only unit/integration tests"
    )
    """Add a custom CLI flag --report to generate coverage reports after tests."""
    parser.addoption("--report", action="store_true", default=False, help="Generate coverage report after tests.")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Run coverage report if --report flag was passed."""
    if session.config.getoption("--report"):
        print("\nGenerating coverage report...")
        try:
            print("\n\n========= COVERAGE FULL REPORT ======================\n\n")
            # TODO: Zachi - Need to understand why it doesn't print to console
            subprocess.run(["poetry", "run", "coverage", "report"], check=True)
            subprocess.run(["poetry", "run", "coverage", "html"], check=True)
            print(
                f"\n====\n\nFull coverage report available on the following link:\n\n  • {os.getcwd()}/htmlcov/index.html\n"
            )
        except subprocess.CalledProcessError as e:
            print(f"Error while generating coverage report: {e}")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


def pytest_collection_modifyitems(config, items):
    # run_all = config.getoption("--all")
    only_e2e_flag = config.getoption("--only-e2e")
    skip_e2e_flag = config.getoption("--skip-e2e")

    skip_non_e2e = pytest.mark.skip(reason="Skipping non-E2E tests (--only-e2e enabled)")
    skip_e2e_marker = pytest.mark.skip(reason="Skipping E2E tests (--skip-e2e enabled)")

    for item in items:
        is_e2e = item.get_closest_marker("e2e") is not None  # More reliable check

        if only_e2e_flag and not is_e2e:
            item.add_marker(skip_non_e2e)  # Skip non-E2E tests if --only-e2e is passed
        elif skip_e2e_flag and is_e2e:
            item.add_marker(skip_e2e_marker)  # Skip E2E tests if --skip-e2e is passed
        # If --all is passed, run all tests without skipping anything


pytest_plugins = ["provisioner_shared.test_lib.fixtures"]
