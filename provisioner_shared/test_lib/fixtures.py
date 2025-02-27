
# from time import sleep
# import docker
import pytest

# from provisioner_shared.test_lib.docker.dockerized import (
#     should_rm_container_after_tests, stop_docker_client, try_stop_and_remove_all_containers_by_name)


# Run the container before running tests suite
@pytest.fixture(scope="session", autouse=True)
def global_poetry_container():
    # Before tests (setup)
    print("\nRunning setup before all tests...")
    
    # Yield control to tests
    yield

    # After tests (teardown)
    print("\nRunning teardown after all tests...")
    
    # client = docker.from_env()
    # should_remove = should_rm_container_after_tests()
    # try_stop_and_remove_all_containers_by_name(client, True)
    # stop_docker_client(client)
    print("\nTeardown completed.")
