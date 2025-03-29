---
layout: docs
title: Testing Overview
description: Learn about the testing framework used in the Provisioner project.
toc: true
---

## Introduction

The Provisioner project uses a comprehensive testing approach that includes unit tests, integration tests, and end-to-end (E2E) tests. This documentation will guide you through the testing framework and how to run tests effectively.

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation. These tests are quick to run and should be the most numerous in the codebase.

### Integration Tests

Integration tests verify that different components work correctly together. They typically test the interaction between two or more units.

### End-to-End (E2E) Tests

E2E tests validate the entire application workflow from start to finish. These tests often involve spinning up Docker containers to simulate remote environments, such as Raspberry Pi nodes.

## Running Tests

The project includes a dedicated test runner script that simplifies running tests across the codebase.

### Basic Usage

```bash
# Run a specific test
./run_tests.py path/to/test.py

# Run all tests
./run_tests.py --all
```

### Docker-based Testing

Tests can be run in Docker containers to provide consistent environments:

```bash
# Run specific test in a container
./run_tests.py path/to/test.py --container

# Run all tests in container
./run_tests.py --all --container
```

### Running E2E Tests

End-to-end tests are marked with `@pytest.mark.e2e` and can be run selectively:

```bash
# Run only E2E tests
./run_tests.py --all --only-e2e

# Skip E2E tests
./run_tests.py --all --skip-e2e
```

For example, to run a specific E2E test for the Raspberry Pi network configuration:

```bash
./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/node/network_cmd_e2e_test.py
```

### Coverage Reports

Generate test coverage reports to identify areas that need more testing:

```bash
# Generate HTML coverage report
./run_tests.py --all --report html

# Generate XML coverage report
./run_tests.py --all --report xml
```

## Writing Tests

When writing tests for the Provisioner project, follow these guidelines:

1. Unit tests should be placed in the same directory as the code they test, with a `_test.py` suffix
2. Mark E2E tests with the `@pytest.mark.e2e` decorator
3. Use the provided test fixtures and utilities from `provisioner_shared.test_lib`

### Example Test

```python
import unittest
import pytest
from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

@pytest.mark.e2e  # Mark as an E2E test
class MyFeatureE2ETestShould(unittest.TestCase):
    
    def test_my_feature_works_correctly(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "my-command",
                "--option1", "value1",
                "--option2", "value2",
            ],
        )
        
        self.assertIn("Expected output", output)
```

## Docker Test Environments

The E2E tests use Docker containers to simulate real environments:

- `provisioner-poetry-e2e` - Used for running Python tests
- `provisioner-remote-ssh` - Used for testing SSH-based interactions
- `provisioner-rpi-os-e2e` - Used for simulating Raspberry Pi OS environments

These Docker images are automatically built and cached for optimal performance.