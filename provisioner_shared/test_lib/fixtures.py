# from time import sleep
# import docker
import os
import pathlib
import shutil

import pytest

PROJECT_ROOT_PATH = str(pathlib.Path(__file__).parent.parent.parent.resolve())


# Run the container before running tests suite
@pytest.fixture(scope="session", autouse=True)
def global_poetry_container():
    # Before tests (setup)
    print("\nRunning setup before all tests...")

    # Yield control to tests
    yield

    # After tests (teardown)
    print("\nRunning teardown after all tests...")

    tests_unit_it_sdists_path = f"{PROJECT_ROOT_PATH}/dockerfiles/poetry/dists"
    if os.path.exists(f"{tests_unit_it_sdists_path}"):
        print(f"Cleaning up Unit/IT tests artifacts in {tests_unit_it_sdists_path}")
        # Cleanup installers plugin Unit/It test artifacts to prevent from multiple versions collision of the same package
        shutil.rmtree(f"{tests_unit_it_sdists_path}")

    tests_e2e_sdists_path = f"{PROJECT_ROOT_PATH}/tests-outputs/installers-plugin/dist"
    if os.path.exists(f"{tests_e2e_sdists_path}"):
        print(f"Cleaning up E2E tests artifacts in {tests_e2e_sdists_path}")
        # Cleanup installers plugin E2E test artifacts to prevent from multiple versions collision of the same package
        shutil.rmtree(f"{tests_e2e_sdists_path}")

    # client = docker.from_env()
    # should_remove = should_rm_container_after_tests()
    # try_stop_and_remove_all_containers_by_name(client, True)
    # stop_docker_client(client)
    print("\nTeardown completed.")
