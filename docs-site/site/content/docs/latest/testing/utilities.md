---
layout: docs
title: Test Utilities
description: Helper utilities to streamline the testing process in the Provisioner project.
toc: true
---

## Test Utilities in Provisioner

The Provisioner project provides several test utilities to make writing and running tests easier and more efficient. These utilities help simulate real-world environments, run CLI commands, and manage test state.

## Core Testing Utilities

### TestEnv

`TestEnv` creates and manages the test environment configuration:

```python
from provisioner_shared.test_lib.test_env import TestEnv

class MyTestCase(unittest.TestCase):
    env = TestEnv.create()
    
    def test_something(self):
        # Use the test environment
        self.assertTrue(self.env.is_ready())
```

### TestCliRunner

`TestCliRunner` simplifies running CLI commands and capturing their output:

```python
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner
from provisioner.main import root_menu

class MyCliTestCase(unittest.TestCase):
    def test_cli_command(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "command",
                "--option1", "value1",
                "--option2", "value2"
            ]
        )
        
        self.assertIn("Expected output", output)
```

## Docker-Based Testing Utilities

### RemoteRPiOsContainer

`RemoteRPiOsContainer` simulates a Raspberry Pi OS environment for end-to-end tests:

```python
from provisioner_shared.test_lib.rpi_os_container import RemoteRPiOsContainer

class RaspberryPiE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = RemoteRPiOsContainer()
        cls.container.start()
        
    @classmethod
    def tearDownClass(cls):
        if cls.container:
            cls.container.stop()
            cls.container = None
            
    def test_connection(self):
        # Test interacting with the container
        self.assertTrue(self.container.is_running())
```

The container exposes several useful properties:

- `container`: The underlying Docker container object
- `ssh_port`: The mapped SSH port for connecting to the container
- `container_id`: The ID of the running container

### RemoteSSHContainer

`RemoteSSHContainer` provides a lightweight SSH server environment for testing remote connections and SSH-based operations:

```python
from provisioner_shared.test_lib.ssh_container import RemoteSSHContainer

class SSHConnectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = RemoteSSHContainer()
        cls.container.start()
        
    @classmethod
    def tearDownClass(cls):
        if cls.container:
            cls.container.stop()
            cls.container = None
            
    def test_ssh_connection(self):
        # Test connecting to the SSH container
        output = TestCliRunner.run(
            root_menu,
            [
                "remote",
                "--connect-mode", "Flags",
                "--username", "user",
                "--password", "password",
                "--host", "127.0.0.1",
                "--port", str(self.container.ssh_port),
                "command"
            ],
        )
        
        self.assertIn("Connection successful", output)
```

Key features of the `RemoteSSHContainer`:

- Standard SSH server with preconfigured credentials
- Pre-mapped port for SSH connections (accessible via `ssh_port` property)
- Designed for testing remote connection workflows
- Simpler than the RPi container when you only need SSH capabilities
- Faster startup times for tests that only require basic SSH functionality

The `RemoteSSHContainer` supports the same core methods as other container utilities:

- `start()`: Starts the container and waits for SSH to be ready
- `stop()`: Stops and removes the container
- `is_running()`: Checks if the container is currently running

### Using Containers in Tests

For end-to-end tests, the containers allow you to:

1. Simulate remote environments without requiring actual hardware
2. Test SSH connections and command execution
3. Verify configuration changes in a controlled environment

Example E2E test with container:

```python
@pytest.mark.e2e
class RaspberryPiNodeNetworkE2ETestShould(unittest.TestCase):
    env = TestEnv.create()

    @classmethod
    def setUpClass(cls):
        cls.container = RemoteRPiOsContainer()
        cls.container.start()

    @classmethod
    def tearDownClass(cls):
        if cls.container:
            cls.container.stop()
            cls.container = None

    def test_e2e_configure_network_settings_successfully(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "single-board",
                "raspberry-pi",
                "node",
                "--environment", "Remote",
                "--connect-mode", "Flags",
                "--node-username", "pi",
                "--node-password", "raspberry",
                "--ip-address", "127.0.0.1",
                "--port", str(self.container.ssh_port),
                # ... other options
            ],
        )
        
        # Assert on expected output
        self.assertIn("Configuration successful", output)
```

## Running E2E Tests

To run E2E tests, use the test runner script with the appropriate flags:

```bash
# Run all E2E tests
./run_tests.py --all --only-e2e

# Run a specific E2E test
./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/node/network_cmd_e2e_test.py
```

## Best Practices

When using test utilities, follow these best practices:

1. **Clean up resources**: Always clean up container resources in `tearDownClass` to avoid resource leaks
2. **Isolate tests**: Make each test independent to prevent test interdependencies
3. **Use appropriate utilities**: Choose the right utilities for your testing needs
4. **Handle errors**: Add proper error handling in setup and teardown methods
5. **Be mindful of performance**: Docker-based tests are more resource-intensive, so use them judiciously