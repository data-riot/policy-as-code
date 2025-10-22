#!/usr/bin/env python3
"""
Policy Validation Script

Validates YAML policies against the policy schema.
Ensures all policies conform to the required structure.
"""

import json
import yaml
import jsonschema
import sys
from pathlib import Path
from typing import Dict, Any, List


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the policy schema from JSON file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def load_yaml_policy(policy_path: str) -> Dict[str, Any]:
    """Load a YAML policy file."""
    with open(policy_path, "r") as f:
        return yaml.safe_load(f)


def validate_policy(policy: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a policy against the schema and return errors."""
    errors = []

    try:
        jsonschema.validate(policy, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")

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


def main():
    """Main validation function."""
    schema_path = "schemas/policy_schema.json"
    policies_dir = Path("examples/policies")

    if not Path(schema_path).exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    schema = load_schema(schema_path)
    all_errors = []

    # Find all YAML policy files (exclude old directory)
    yaml_files = list(policies_dir.glob("*.yaml")) + list(policies_dir.glob("*.yml"))

    if not yaml_files:
        print("No YAML policy files found")
        sys.exit(0)

    print(f"Validating {len(yaml_files)} policy files...")

    for policy_file in yaml_files:
        print(f"Validating {policy_file}...")

        try:
            policy = load_yaml_policy(str(policy_file))

            # Run all validation checks
            errors = []
            errors.extend(validate_policy(policy, schema))
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

    if all_errors:
        print(f"\n❌ Validation failed with {len(all_errors)} errors:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(yaml_files)} policies validated successfully!")


if __name__ == "__main__":
    main()
