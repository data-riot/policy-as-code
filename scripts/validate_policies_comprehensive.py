#!/usr/bin/env python3
"""
Comprehensive Policy Validation Script

Validates policies using both JSON Schema and SHACL (JSON-LD) approaches.
Supports both traditional YAML policies and semantic web JSON-LD policies.
"""

import json
import yaml
import jsonschema
import sys
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import tempfile
import os


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the policy schema from JSON file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def load_yaml_policy(policy_path: str) -> Dict[str, Any]:
    """Load a YAML policy file."""
    with open(policy_path, "r") as f:
        return yaml.safe_load(f)


def load_jsonld_policy(policy_path: str) -> Dict[str, Any]:
    """Load a JSON-LD policy file."""
    with open(policy_path, "r") as f:
        return json.load(f)


def validate_with_json_schema(
    policy: Dict[str, Any], schema: Dict[str, Any]
) -> List[str]:
    """Validate a policy against the JSON schema."""
    errors = []

    try:
        jsonschema.validate(policy, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"JSON Schema validation error: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")

    return errors


def validate_with_shacl(jsonld_policy: Dict[str, Any], shape_file: str) -> List[str]:
    """Validate a JSON-LD policy against SHACL shapes."""
    errors = []

    try:
        # Create temporary file for the JSON-LD policy
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonld", delete=False
        ) as tmp_file:
            # Fix context path to be absolute
            if "@context" in jsonld_policy and isinstance(
                jsonld_policy["@context"], str
            ):
                if jsonld_policy["@context"].startswith("../../"):
                    # Convert relative path to absolute
                    context_path = Path(jsonld_policy["@context"]).resolve()
                    jsonld_policy_copy = jsonld_policy.copy()
                    jsonld_policy_copy["@context"] = str(context_path)
                    json.dump(jsonld_policy_copy, tmp_file, indent=2)
                else:
                    json.dump(jsonld_policy, tmp_file, indent=2)
            else:
                json.dump(jsonld_policy, tmp_file, indent=2)
            tmp_path = tmp_file.name

        # Run pyshacl validation
        result = subprocess.run(
            ["python3", "-m", "pyshacl", "-s", shape_file, "-df", "json-ld", tmp_path],
            capture_output=True,
            text=True,
        )

        # Clean up temporary file
        os.unlink(tmp_path)

        if result.returncode != 0:
            errors.append(f"SHACL validation error: {result.stderr}")

    except FileNotFoundError:
        errors.append("pyshacl not found. Install with: pip install pyshacl")
    except Exception as e:
        errors.append(f"SHACL validation error: {str(e)}")

    return errors


def check_required_fields(policy: Dict[str, Any]) -> List[str]:
    """Check for required fields in the policy."""
    errors = []

    required_fields = [
        "id",
        "version",
        "name",
        "description",
        "owner",
        "law_reference",
        "inputs_schema",
        "outputs_schema",
        "decision_logic",
        "metadata",
    ]

    for field in required_fields:
        if field not in policy:
            errors.append(f"Missing required field: {field}")

    return errors


def check_law_reference_eli(policy: Dict[str, Any]) -> List[str]:
    """Check that law_reference.eli is properly formatted."""
    errors = []

    if "law_reference" in policy:
        law_ref = policy["law_reference"]
        if "eli" in law_ref:
            eli_uri = law_ref["eli"]
            if not eli_uri.startswith("https://finlex.fi/eli/laki/"):
                errors.append(f"Invalid ELI URI format: {eli_uri}")
        else:
            errors.append("Missing law_reference.eli field")

    return errors


def check_decision_logic_rules(policy: Dict[str, Any]) -> List[str]:
    """Check that decision logic has proper rules structure."""
    errors = []

    if "decision_logic" in policy:
        logic = policy["decision_logic"]
        if "rules" in logic:
            rules = logic["rules"]
            if not isinstance(rules, list) or len(rules) == 0:
                errors.append("decision_logic.rules must be a non-empty array")

            for i, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    errors.append(f"Rule {i} must be an object")
                    continue

                required_rule_fields = ["name", "description", "conditions", "result"]
                for field in required_rule_fields:
                    if field not in rule:
                        errors.append(f"Rule {i} missing required field: {field}")

                # Check that result has approved field
                if "result" in rule and "approved" not in rule["result"]:
                    errors.append(f"Rule {i} result missing 'approved' field")
        else:
            errors.append("decision_logic missing 'rules' field")

    return errors


def check_default_deny(policy: Dict[str, Any]) -> List[str]:
    """Check that policy enforces default deny."""
    errors = []

    if "decision_logic" in policy:
        logic = policy["decision_logic"]
        if "default_result" in logic:
            default_result = logic["default_result"]
            if "approved" in default_result and default_result["approved"] is True:
                errors.append(
                    "Default result should deny (approved: false) for security"
                )
        else:
            errors.append(
                "Missing default_result - required for default deny enforcement"
            )

    return errors


def validate_jsonld_policy(policy_path: Path) -> List[str]:
    """Validate a JSON-LD policy file."""
    errors = []

    try:
        policy = load_jsonld_policy(str(policy_path))

        # Check basic JSON-LD structure
        if "@context" not in policy:
            errors.append("Missing @context field")

        if "@type" not in policy:
            errors.append("Missing @type field")

        if "@id" not in policy and "id" not in policy:
            errors.append("Missing @id or id field")

        # Validate with SHACL if it's a Policy type
        if policy.get("@type") == "Policy" or policy.get("type") == "Policy":
            shape_file = "schemas/policy_shape.ttl"
            if Path(shape_file).exists():
                shacl_errors = validate_with_shacl(policy, shape_file)
                errors.extend(shacl_errors)

    except Exception as e:
        errors.append(f"Error loading JSON-LD policy: {str(e)}")

    return errors


def main():
    """Main validation function."""
    schema_path = "schemas/policy_schema.json"
    policies_dir = Path("examples/policies")

    if not Path(schema_path).exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    schema = load_schema(schema_path)
    all_errors = []

    # Find all policy files
    yaml_files = list(policies_dir.glob("*.yaml")) + list(policies_dir.glob("*.yml"))
    jsonld_files = list(policies_dir.glob("*.jsonld"))

    total_files = len(yaml_files) + len(jsonld_files)

    if total_files == 0:
        print("No policy files found")
        sys.exit(0)

    print(f"Validating {total_files} policy files...")

    # Validate YAML policies with JSON schema
    for policy_file in yaml_files:
        print(f"Validating {policy_file}...")

        try:
            policy = load_yaml_policy(str(policy_file))

            # Run all validation checks
            errors = []
            errors.extend(validate_with_json_schema(policy, schema))
            errors.extend(check_required_fields(policy))
            errors.extend(check_law_reference_eli(policy))
            errors.extend(check_decision_logic_rules(policy))
            errors.extend(check_default_deny(policy))

            if errors:
                print(f"  ❌ {len(errors)} errors found:")
                for error in errors:
                    print(f"    - {error}")
                all_errors.extend([f"{policy_file}: {error}" for error in errors])
            else:
                print(f"  ✅ Valid")

        except Exception as e:
            error_msg = f"Error loading {policy_file}: {str(e)}"
            print(f"  ❌ {error_msg}")
            all_errors.append(error_msg)

    # Validate JSON-LD policies with SHACL
    for policy_file in jsonld_files:
        print(f"Validating {policy_file}...")

        errors = validate_jsonld_policy(policy_file)

        if errors:
            print(f"  ❌ {len(errors)} errors found:")
            for error in errors:
                print(f"    - {error}")
            all_errors.extend([f"{policy_file}: {error}" for error in errors])
        else:
            print(f"  ✅ Valid")

    if all_errors:
        print(f"\n❌ Validation failed with {len(all_errors)} errors:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✅ All {total_files} policies validated successfully!")


if __name__ == "__main__":
    main()
