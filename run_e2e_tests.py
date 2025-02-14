#!/usr/bin/env python3

import json
import sys

import docker


def build_and_run_tests(test_target=None):
    client = docker.from_env()

    # Build the Docker image
    print("Building Docker image for E2E tests...")
    # Build the Docker image
    build_logs = client.api.build(
        path=".",  # Build context
        dockerfile="./Dockerfile",  # Specify the Dockerfile
        tag="provisioner-e2e:latest",  # Image tag
        rm=True,  # Remove intermediate containers
    )

    print("====================================++")

    # Stream and display the logs
    for log in build_logs:
        try:
            log_line = json.loads(log.decode("utf-8"))
            if "stream" in log_line:
                print(log_line["stream"].strip())
        except json.JSONDecodeError:
            print(log.decode("utf-8").strip())

    # Define the default or specific test command
    test_command = ["poetry", "run", "coverage", "run", "-m", "pytest"]
    if test_target:
        test_command.append(test_target)
    print(f"Running tests with command: {' '.join(test_command)}")

    try:
        # Run the container with the test command
        container = client.containers.run(
            "provisioner-e2e:latest",
            command=test_command,
            # remove=True,
            stdout=True,
            stderr=True,
            detach=True,
        )
        # Wait for the container to finish and retrieve its logs
        logs = container.logs(follow=True).decode("utf-8")
        print("Test Results:")
        print(logs)

        # Clean up: Remove the container manually after processing logs
        container.remove()

    except docker.errors.ContainerError as e:
        # Print detailed error logs using e.container.logs()
        print(f"ContainerError: The command '{e.command}' failed with exit code {e.exit_status}")
        print("Container Logs:")
        print(e.container.logs().decode("utf-8"))  # Retrieve logs from the container
        raise

    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
        raise


if __name__ == "__main__":
    # Accept a specific test target from the command line
    test_target = sys.argv[1] if len(sys.argv) > 1 else None
    build_and_run_tests(test_target)
