#!/usr/bin/env python3
"""
Package Naming Validation Script

Ensures all Rego packages follow the naming convention:
org.policy_as_code.<policy_name>.v<version>
"""

import re
import sys
from pathlib import Path
from typing import List


def validate_package_naming(file_path: Path) -> List[str]:
    """Validate package naming convention in a Rego file."""
    errors = []

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading file: {e}"]

    # Find package declaration
    package_match = re.search(r"^package\s+([a-zA-Z0-9_.]+)", content, re.MULTILINE)

    if not package_match:
        errors.append("Missing package declaration")
        return errors

    package_name = package_match.group(1)

    # Validate naming convention
    expected_pattern = r"^org\.policy_as_code\.[a-z0-9_]+\.v[0-9]+$"

    if not re.match(expected_pattern, package_name):
        errors.append(
            f"Invalid package naming: '{package_name}'. Expected format: org.policy_as_code.<policy_name>.v<version>"
        )

    # Check for specific components
    parts = package_name.split(".")

    if len(parts) != 4:
        errors.append(
            f"Package name should have 4 parts separated by dots, got {len(parts)}"
        )
        return errors

    # Check organization
    if parts[0] != "org":
        errors.append(f"First part should be 'org', got '{parts[0]}'")

    # Check project name
    if parts[1] != "policy_as_code":
        errors.append(f"Second part should be 'policy_as_code', got '{parts[1]}'")

    # Check policy name
    policy_name = parts[2]
    if not re.match(r"^[a-z0-9_]+$", policy_name):
        errors.append(
            f"Policy name '{policy_name}' should contain only lowercase letters, numbers, and underscores"
        )

    # Check version
    version = parts[3]
    if not version.startswith("v"):
        errors.append(f"Version should start with 'v', got '{version}'")
    elif not re.match(r"^v[0-9]+$", version):
        errors.append(f"Version '{version}' should be 'v' followed by numbers only")

    return errors


def main():
    """Main function to validate package naming in all Rego files."""
    policies_dir = Path("policies/rego")

    if not policies_dir.exists():
        print(f"Error: Policies directory not found: {policies_dir}")
        sys.exit(1)

    # Find all Rego files
    rego_files = list(policies_dir.glob("**/*.rego"))

    if not rego_files:
        print("No Rego files found")
        sys.exit(0)

    print(f"Validating package naming in {len(rego_files)} Rego files...")

    all_errors = []

    for rego_file in rego_files:
        print(f"Checking {rego_file}...")

        errors = validate_package_naming(rego_file)

        if errors:
            print(f"  ❌ {len(errors)} issues found:")
            for error in errors:
                print(f"    - {error}")
            all_errors.extend([f"{rego_file}: {error}" for error in errors])
        else:
            print(f"  ✅ Package naming valid")

    if all_errors:
        print(f"\n❌ Package naming validation failed with {len(all_errors)} issues:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(rego_files)} Rego files have valid package naming!")


if __name__ == "__main__":
    main()
