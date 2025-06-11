# Version Compatibility System

This document describes the version compatibility system that ensures plugins work correctly with specific runtime versions.

## Overview

The version compatibility system addresses the challenge of maintaining compatibility between the Provisioner runtime and its plugins. It provides:

1. **Automatic Version Checking**: Runtime automatically filters incompatible plugins during loading
2. **Plugin Manifests**: Plugins declare their compatible runtime version ranges
3. **Semantic Versioning**: Uses standard semantic versioning for compatibility checks
4. **CLI Tools**: Commands to check and manage plugin compatibility

## How It Works

### Plugin Manifests

Each plugin can include a `plugin-manifest.json` file in its `resources/` directory that declares:

```json
{
  "plugin_name": "provisioner_my_plugin",
  "plugin_version": "0.1.0",
  "runtime_version_range": ">=0.1.15,<0.2.0",
  "description": "My awesome plugin",
  "author": "Your Name",
  "maintainer": "Your Name",
  "compatibility_notes": "Requires runtime 0.1.15+ for new API features"
}
```

### Version Range Formats

The system supports several version range formats:

| Format | Example | Description |
|--------|---------|-------------|
| Exact | `1.2.3` | Exact version match |
| Minimum | `>=1.0.0` | Minimum version required |
| Range | `>=1.0.0,<2.0.0` | Version range (AND condition) |
| Caret | `^1.2.0` | Compatible within minor (>=1.2.0,<2.0.0) |
| Tilde | `~1.2.0` | Compatible within patch (>=1.2.0,<1.3.0) |

### Automatic Filtering

When the runtime loads plugins, it:

1. Detects the current runtime version
2. Scans installed plugins for compatibility manifests
3. Filters out incompatible plugins
4. Loads only compatible plugins

## Usage

### For Plugin Developers

#### 1. Create a Plugin Manifest

Create `your_plugin/resources/plugin-manifest.json`:

```bash
# Using the helper script
./scripts/plugin_manifest_helper.py create \
  --plugin-name provisioner_my_plugin \
  --plugin-version 0.1.0 \
  --runtime-range ">=0.1.15,<0.2.0" \
  --output plugins/provisioner_my_plugin/provisioner_my_plugin/resources/plugin-manifest.json
```

#### 2. Validate Your Manifest

```bash
./scripts/plugin_manifest_helper.py validate \
  plugins/provisioner_my_plugin/provisioner_my_plugin/resources/plugin-manifest.json
```

#### 3. Test Compatibility

```bash
./scripts/plugin_manifest_helper.py test \
  plugins/provisioner_my_plugin/provisioner_my_plugin/resources/plugin-manifest.json \
  --runtime-version 0.1.18
```

### For Runtime Users

#### Check Plugin Compatibility

```bash
# Show compatible plugins only
provisioner plugins compatibility

# Show all plugins including incompatible ones
provisioner plugins compatibility --show-incompatible
```

#### List Installed Plugins

The `provisioner plugins list` command now automatically filters to show only compatible plugins.

#### Install Plugins  

```bash
# Interactive selection from configured plugins
provisioner plugins install

# Install specific plugin by name
provisioner plugins install --name provisioner-docker-plugin
```

## Implementation Details

### Core Components

1. **VersionCompatibility Class** (`provisioner_shared/components/runtime/utils/version_compatibility.py`)
   - Handles version parsing and range checking
   - Supports semantic versioning standards
   - Provides plugin compatibility validation

2. **Enhanced PackageLoader** (`provisioner_shared/components/runtime/utils/package_loader.py`)
   - Automatically applies version filtering during plugin discovery
   - Provides both filtered and unfiltered plugin loading methods

3. **Plugin CLI Commands** (`provisioner_shared/components/runtime/command/plugins/cli.py`)
   - New `compatibility` command for checking plugin compatibility
   - Enhanced plugin listing with version awareness
   - Plugin installation with version filtering

### Backward Compatibility

- **No Manifest = Compatible**: Plugins without manifests are assumed compatible
- **Graceful Degradation**: System continues to work if version detection fails
- **Existing Plugins**: All existing plugins continue to work without modification

### Version Detection

The runtime version is detected using multiple fallback methods:

1. **Pip Package**: Check installed `provisioner-runtime` package version
2. **Local File**: Read from `provisioner/resources/version.txt` (development)  
3. **PyPI Fallback**: Query PyPI for `provisioner-runtime` package version (if not installed locally)
4. **Fallback**: Assume compatibility if version cannot be determined

## Examples

### Example 1: Basic Plugin Manifest

```json
{
  "plugin_name": "provisioner_installers_plugin",
  "plugin_version": "0.1.6",
  "runtime_version_range": ">=0.1.15,<0.2.0",
  "description": "Install anything anywhere on any OS/Arch",
  "author": "Zachi Nachshon",
  "maintainer": "Zachi Nachshon",
  "compatibility_notes": "Requires runtime 0.1.15+ for enhanced installer API"
}
```

### Example 2: Flexible Compatibility

```json
{
  "plugin_name": "provisioner_examples_plugin",
  "plugin_version": "0.1.8",
  "runtime_version_range": "^0.1.0",
  "description": "Example plugin with broad compatibility",
  "author": "Zachi Nachshon",
  "maintainer": "Zachi Nachshon",
  "compatibility_notes": "Compatible with all 0.1.x runtime versions"
}
```

### Example 3: Strict Version Requirements

```json
{
  "plugin_name": "provisioner_advanced_plugin",
  "plugin_version": "1.0.0",
  "runtime_version_range": ">=0.1.20,<0.1.25",
  "description": "Plugin requiring specific runtime features",
  "author": "Developer",
  "maintainer": "Developer",
  "compatibility_notes": "Requires specific runtime features available only in 0.1.20-0.1.24"
}
```

## Best Practices

### For Plugin Developers

1. **Be Specific**: Use precise version ranges that reflect actual compatibility
2. **Test Thoroughly**: Test your plugin with the minimum and maximum supported runtime versions
3. **Document Changes**: Update compatibility ranges when making breaking changes
4. **Use Semantic Versioning**: Follow semantic versioning for your plugin versions

### Version Range Guidelines

- **Major Version Changes**: Use `>=X.Y.Z,<(X+1).0.0` for major version boundaries
- **Minor Version Features**: Use `>=X.Y.Z` if you need specific minor version features
- **Patch Compatibility**: Use `^X.Y.Z` for broad compatibility within a major version
- **Conservative Approach**: Start with narrow ranges and expand based on testing

### For Runtime Developers

1. **Semantic Versioning**: Follow semantic versioning for runtime releases
2. **Breaking Changes**: Increment major version for breaking plugin API changes
3. **Feature Additions**: Increment minor version for new plugin API features
4. **Bug Fixes**: Increment patch version for bug fixes that don't affect plugin API

## Troubleshooting

### Plugin Not Loading

1. Check if plugin is compatible:
   ```bash
   provisioner plugins compatibility --show-incompatible
   ```

2. Validate plugin manifest:
   ```bash
   ./scripts/plugin_manifest_helper.py validate path/to/plugin-manifest.json
   ```

3. Check runtime version:
   ```bash
   provisioner version
   ```

### Common Issues

- **Missing Manifest**: Plugin assumed compatible but may not work correctly
- **Invalid Version Range**: Syntax errors in version range specification
- **Runtime Version Detection**: Runtime version cannot be determined

### Debug Mode

Enable debug logging to see detailed compatibility checking:

```bash
PROVISIONER_PRE_INIT_DEBUG=true provisioner plugins list
```

## Migration Guide

### Existing Plugins

1. **Add Manifest**: Create `plugin-manifest.json` in your plugin's `resources/` directory
2. **Test Compatibility**: Validate against current and future runtime versions
3. **Update CI/CD**: Include manifest validation in your build process

### Existing Users

- **No Action Required**: System is backward compatible
- **Optional**: Use new compatibility commands to check plugin status
- **Recommended**: Update plugins to include manifests for better compatibility tracking

## Future Enhancements

- **Automatic Updates**: Suggest compatible plugin updates
- **Dependency Resolution**: Handle plugin-to-plugin dependencies  
- **Version Constraints**: Allow runtime to specify minimum plugin versions 