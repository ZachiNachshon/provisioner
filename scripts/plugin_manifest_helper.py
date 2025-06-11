#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from provisioner_shared.components.runtime.utils.version_compatibility import VersionCompatibility


def create_manifest_template(plugin_name: str, plugin_version: str, runtime_version_range: str) -> Dict[str, Any]:
    """Create a template plugin manifest"""
    return {
        "name": plugin_name,
        "version": plugin_version,
        "runtime_version_range": runtime_version_range,
        "description": "Plugin description here",
        "author": "Your Name",
        "maintainer": "Your Name",
        "compatibility_notes": "Add notes about compatibility requirements or limitations",
    }


def validate_manifest(manifest_path: Path) -> bool:
    """Validate a plugin manifest file"""
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Check required fields - support both old and new field names for backward compatibility
        name_field = manifest.get("name") or manifest.get("plugin_name")
        version_field = manifest.get("version") or manifest.get("plugin_version")

        if not name_field:
            print("❌ Missing required field: 'name' (or 'plugin_name' for old format)")
            return False

        if not version_field:
            print("❌ Missing required field: 'version' (or 'plugin_version' for old format)")
            return False

        # runtime_version_range is optional for runtime manifests, required for plugins
        version_range = manifest.get("runtime_version_range")
        if version_range:
            try:
                # Test with a dummy version to validate the range format
                VersionCompatibility.version_satisfies_range("1.0.0", version_range)
                print(f"✅ Version range format is valid: {version_range}")
            except Exception as e:
                print(f"❌ Invalid version range format '{version_range}': {e}")
                return False

        # Validate plugin version format
        try:
            VersionCompatibility.parse_version(version_field)
            print(f"✅ Version format is valid: {version_field}")
        except Exception as e:
            print(f"❌ Invalid version format '{version_field}': {e}")
            return False

        print(f"✅ Manifest validation passed for {name_field}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Manifest file not found: {manifest_path}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def test_compatibility(manifest_path: Path, runtime_version: str) -> bool:
    """Test if a plugin is compatible with a specific runtime version"""
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        version_range = manifest.get("runtime_version_range")
        plugin_name = manifest.get("name") or manifest.get("plugin_name")

        if not version_range:
            print(f"ℹ️  Plugin {plugin_name} has no runtime version range specified (assuming compatible)")
            return True

        is_compatible = VersionCompatibility.version_satisfies_range(runtime_version, version_range)

        if is_compatible:
            print(f"✅ Plugin {plugin_name} is compatible with runtime {runtime_version}")
        else:
            print(f"❌ Plugin {plugin_name} is NOT compatible with runtime {runtime_version}")
            print(f"   Required: {version_range}")
            print(f"   Provided: {runtime_version}")

        return is_compatible

    except Exception as e:
        print(f"❌ Error testing compatibility: {e}")
        return False


def create_manifest(plugin_name: str, plugin_version: str, runtime_version_range: str, output_path: Path):
    """Create a new plugin manifest file"""
    manifest = create_manifest_template(plugin_name, plugin_version, runtime_version_range)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Created plugin manifest: {output_path}")
    print("📝 Please edit the manifest to add proper description, author, and compatibility notes")


def main():
    parser = argparse.ArgumentParser(description="Plugin manifest helper utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new plugin manifest")
    create_parser.add_argument("--plugin-name", required=True, help="Plugin name (e.g., provisioner_my_plugin)")
    create_parser.add_argument("--plugin-version", required=True, help="Plugin version (e.g., 0.1.0)")
    create_parser.add_argument("--runtime-range", required=True, help="Runtime version range (e.g., >=0.1.0,<0.2.0)")
    create_parser.add_argument("--output", required=True, help="Output path for the manifest file")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a plugin manifest")
    validate_parser.add_argument("manifest", help="Path to the plugin manifest file")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test plugin compatibility with a runtime version")
    test_parser.add_argument("manifest", help="Path to the plugin manifest file")
    test_parser.add_argument("--runtime-version", required=True, help="Runtime version to test against")

    # Examples command
    subparsers.add_parser("examples", help="Show version range examples")

    args = parser.parse_args()

    if args.command == "create":
        output_path = Path(args.output)
        create_manifest(args.plugin_name, args.plugin_version, args.runtime_range, output_path)

    elif args.command == "validate":
        manifest_path = Path(args.manifest)
        success = validate_manifest(manifest_path)
        sys.exit(0 if success else 1)

    elif args.command == "test":
        manifest_path = Path(args.manifest)
        success = test_compatibility(manifest_path, args.runtime_version)
        sys.exit(0 if success else 1)

    elif args.command == "examples":
        print("Version Range Examples:")
        print("  >=1.0.0,<2.0.0  - Compatible with 1.x versions only")
        print("  ^1.2.0          - Compatible with 1.2.0 to 1.x.x (caret range)")
        print("  ~1.2.0          - Compatible with 1.2.0 to 1.2.x (tilde range)")
        print("  >=1.0.0         - Minimum version 1.0.0")
        print("  1.2.3           - Exact version match")
        print("")
        print("Testing examples:")
        examples = [
            ("1.5.0", ">=1.0.0,<2.0.0", True),
            ("2.0.0", ">=1.0.0,<2.0.0", False),
            ("1.3.5", "^1.2.0", True),
            ("2.0.0", "^1.2.0", False),
            ("1.2.5", "~1.2.0", True),
            ("1.3.0", "~1.2.0", False),
        ]

        for version, range_spec, expected in examples:
            result = VersionCompatibility.version_satisfies_range(version, range_spec)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {version} satisfies {range_spec}: {result}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
