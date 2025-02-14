import pytest


# pytest hook that allows to exclude or include E2E tests based tests decorators
# Should run on CI but not locally
# Use 'poetry run pytest --help | grep e2e' to verify that the marker is available
def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", default=False, help="Run only E2E tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--e2e"):
        # Skip tests marked with 'e2e' if --e2e is NOT passed
        skip_e2e = pytest.mark.skip(reason="Skipping E2E tests (use --e2e to run)")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
