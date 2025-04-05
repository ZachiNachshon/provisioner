---
layout: docs
title: Test Assertions
description: Learn about assertion utilities and best practices for testing in the Provisioner project.
toc: true
---

## Test Assertions in Provisioner

Assertions are vital components of effective tests. The Provisioner project uses Python's unittest framework along with custom assertion utilities to make tests more readable and maintainable.

## Standard Assertions

The unittest framework provides many powerful assertion methods:

### Basic Assertions

```python
# Test equality
self.assertEqual(expected, actual)
self.assertNotEqual(unexpected, actual)

# Test boolean values
self.assertTrue(expression)
self.assertFalse(expression)

# Test for None/not None
self.assertIsNone(value)
self.assertIsNotNone(value)
```

### String Assertions

When testing CLI outputs, string assertions are particularly useful:

```python
# Test that string contains a substring
self.assertIn("expected text", output)
self.assertNotIn("unexpected text", output)

# Test string equality
self.assertEqual("expected string", actual_string)

# Test regex patterns
self.assertRegex(string, r"regex_pattern")
```

## Custom Assertion Utilities

The Provisioner framework includes custom assertion utilities to simplify common testing scenarios.

### CLI Output Assertions

When testing CLI command outputs, you can use these patterns:

```python
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

# Run a CLI command and assert on its output
output = TestCliRunner.run(
    root_menu,
    ["single-board", "raspberry-pi", "node", "configure"],
)

# Assert configuration was successful
self.assertIn("Mock raspi-config: do_boot_behaviour B1", output)
self.assertIn("Configuration completed successfully", output)
```

### File System Assertions

For tests that interact with the file system:

```python
# Check if a file was created
self.assertTrue(os.path.exists(file_path))

# Check file content
with open(file_path, 'r') as f:
    content = f.read()
    self.assertIn("expected content", content)
```

## Best Practices

When writing assertions in your tests, follow these best practices:

1. **Be specific**: Test exactly what you need to, no more, no less
2. **Clear failure messages**: Use custom failure messages to make debugging easier
   ```python
   self.assertTrue(condition, "Failure message with context")
   ```
   
3. **Test one thing per test**: Each test method should verify a single aspect of behavior

4. **Consider edge cases**: Don't just test the "happy path"; test edge cases and error conditions

5. **Use appropriate assertions**: Choose the most appropriate assertion for your needs (e.g., use `assertIn` for substring checks instead of regex when possible)

## Examples from Real Tests

Here are examples of assertions from the Raspberry Pi E2E tests:

```python
# From configure_cmd_e2e_test.py
def test_e2e_install_anchor_on_remote_successfully(self):
    output = TestCliRunner.run(
        root_menu,
        [
            "single-board",
            "raspberry-pi",
            "node",
            # ... other arguments ...
            "configure",
        ],
    )

    self.assertIn("Mock raspi-config: do_boot_behaviour B1", output)
    self.assertIn("Mock raspi-config: do_ssh 0", output)
    self.assertIn("Mock raspi-config: do_camera 1", output)
    self.assertIn("Mock raspi-config: do_spi 1", output)
    self.assertIn("Mock raspi-config: do_i2c 1", output)
    self.assertIn("Mock raspi-config: do_serial 1", output)
```

```python
# From network_cmd_e2e_test.py
def test_e2e_configure_network_settings_successfully(self):
    output = TestCliRunner.run(
        root_menu,
        [
            "single-board",
            "raspberry-pi",
            "node",
            # ... other arguments ...
            "network",
            "--static-ip-address", "1.1.1.200",
            "--gw-ip-address", "1.1.1.1",
            "--dns-ip-address", "192.168.1.1",
        ],
    )

    # Verify the configuration commands were executed
    self.assertIn("Mock raspi-config: do_hostname test-node", output)
    self.assertIn("Mock raspi-config: do_wifi_country IL", output)
```

## Custom Assertion Utilities

The Provisioner project includes a set of custom assertion utilities in the `provisioner_shared/test_lib/assertions.py` file that simplify common testing patterns. These utilities are designed to make tests more readable, maintainable, and expressive.

## Available Assertion Methods

### expect_call_argument

Verifies that a mocked method was called with a specific argument value:

```python
from provisioner_shared.test_lib.assertions import Assertion
from unittest import mock

# Setup a mock
mock_object = mock.MagicMock()
mock_object.some_method(name="test", value=42)

# Verify argument value
Assertion.expect_call_argument(self, mock_object.some_method, "name", "test")
Assertion.expect_call_argument(self, mock_object.some_method, "value", 42)
```

### expect_exists

Verifies that a particular argument was provided in a method call:

```python
# Using the same mock from previous example
Assertion.expect_exists(self, mock_object.some_method, "name")
```

### expect_call_arguments

Applies a custom verification function to a method call argument:

```python
def custom_validation(value):
    assert value > 0, "Value must be positive"

Assertion.expect_call_arguments(
    self, 
    mock_object.some_method, 
    "value", 
    custom_validation
)
```

### expect_raised_failure

Verifies that a method raises a specific exception type:

```python
def method_that_fails():
    raise ValueError("Test error")

Assertion.expect_raised_failure(self, ValueError, method_that_fails)
```

For testing Click commands that fail:

```python
def run_failing_command():
    return TestCliRunner.run(root_menu, ["command", "--invalid-option"])

Assertion.expect_raised_failure(self, SystemExit, run_failing_command)
```

### expect_output

Verifies that a method's output contains an expected string, cleaning any ANSI color codes:

```python
def run_command():
    return TestCliRunner.run(root_menu, ["command", "--option", "value"])

Assertion.expect_output(self, "Expected output text", run_command)
```

### expect_outputs

Similar to `expect_output` but verifies multiple expected strings in the output:

```python
expected_outputs = [
    "First expected text",
    "Second expected text",
    "Third expected text"
]

Assertion.expect_outputs(self, expected_outputs, run_command)
```

### expect_success

Verifies that a method executes without raising exceptions:

```python
def method_that_should_succeed():
    return "success"

result = Assertion.expect_success(self, method_that_should_succeed)
self.assertEqual(result, "success")  # Can use the returned value
```

### expect_equal_objects

Compares two objects for equality by converting them to JSON:

```python
class TestObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value

obj1 = TestObject("test", 42)
obj2 = TestObject("test", 42)
obj3 = TestObject("different", 100)

# Should pass
Assertion.expect_equal_objects(self, obj1, obj2)

# Should fail
Assertion.expect_equal_objects(self, obj1, obj3)
```

This is particularly useful for comparing complex objects or objects that don't implement `__eq__`.

## Handling ANSI Color Codes

The assertion utilities automatically handle ANSI color codes in command outputs, making it easier to test colorized console output:

```python
# This works even if the output contains ANSI color codes
def run_colorized_command():
    return TestCliRunner.run(root_menu, ["command", "--colorized"])

Assertion.expect_output(self, "Expected plain text", run_colorized_command)
```

## Using Assertions in E2E Tests

End-to-end tests often need to verify CLI output. Here's an example from a Raspberry Pi network configuration test:

```python
def test_e2e_configure_network_settings_successfully(self):
    def run_cmd():
        return TestCliRunner.run(
            root_menu,
            [
                "single-board",
                "raspberry-pi",
                "node",
                # ... other arguments ...
                "network",
            ],
        )
    
    expected_outputs = [
        "Mock raspi-config: do_hostname test-node",
        "Mock raspi-config: do_wifi_country IL",
    ]
    
    Assertion.expect_outputs(self, expected_outputs, run_cmd)
```

## Best Practices

When using these custom assertions:

1. **Choose the most specific assertion**: Use the most specific assertion method for your test case
2. **Error messages**: The assertions provide detailed error messages when they fail
3. **Mock verification**: For mocks, verify both that methods were called and with the correct arguments
4. **Object comparison**: Use `expect_equal_objects` for complex object comparison instead of direct equality checks
5. **Command output**: Use `expect_output` or `expect_outputs` when testing CLI commands