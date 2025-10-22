#!/usr/bin/env python3
"""
Rego Metadata Checker

Ensures all Rego files have required metadata blocks.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def check_rego_metadata(file_path: Path) -> List[str]:
    """Check if a Rego file has required metadata."""
    errors = []

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading file: {e}"]

    # Check for package declaration
    package_match = re.search(r"^package\s+([a-zA-Z0-9_.]+)", content, re.MULTILINE)
    if not package_match:
        errors.append("Missing package declaration")
    else:
        package_name = package_match.group(1)
        # Check package naming convention
        if not re.match(r"^org\.policy_as_code\.[a-z0-9_]+\.v[0-9]+$", package_name):
            errors.append(
                f"Invalid package naming convention: {package_name}. Expected: org.policy_as_code.<policy_name>.v<version>"
            )

    # Check for metadata block
    metadata_start = content.find("# Metadata block")
    if metadata_start == -1:
        errors.append("Missing metadata block comment")
        return errors

    # Extract metadata section
    lines = content[metadata_start:].split("\n")
    metadata_lines = []
    in_metadata = False

    for line in lines:
        if line.strip().startswith("# Metadata block"):
            in_metadata = True
            continue
        elif in_metadata:
            if line.strip().startswith("#"):
                metadata_lines.append(line.strip()[1:].strip())
            else:
                break

    # Check required metadata fields
    required_fields = [
        "owner",
        "version",
        "description",
        "created_date",
        "last_updated",
    ]

    metadata_dict = {}
    for line in metadata_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            metadata_dict[key.strip()] = value.strip()

    for field in required_fields:
        if field not in metadata_dict:
            errors.append(f"Missing required metadata field: {field}")

    # Check for default deny (skip test files)
    if (
        not file_path.name.endswith("_test.rego")
        and "default allow := false" not in content
    ):
        errors.append("Missing explicit default deny: 'default allow := false'")

    return errors


def main():
    """Main function to check all Rego files."""
    policies_dir = Path("policies/rego")

    if not policies_dir.exists():
        print(f"Error: Policies directory not found: {policies_dir}")
        sys.exit(1)

    # Find all Rego files
    rego_files = list(policies_dir.glob("**/*.rego"))

    if not rego_files:
        print("No Rego files found")
        sys.exit(0)

    print(f"Checking metadata in {len(rego_files)} Rego files...")

    all_errors = []

    for rego_file in rego_files:
        print(f"Checking {rego_file}...")

        errors = check_rego_metadata(rego_file)

        if errors:
            print(f"  ❌ {len(errors)} issues found:")
            for error in errors:
                print(f"    - {error}")
            all_errors.extend([f"{rego_file}: {error}" for error in errors])
        else:
            print(f"  ✅ Metadata valid")

    if all_errors:
        print(f"\n❌ Metadata check failed with {len(all_errors)} issues:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(rego_files)} Rego files have valid metadata!")


if __name__ == "__main__":
    main()
