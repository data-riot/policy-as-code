#!/usr/bin/env python3
"""
YAML Decision Example

This example shows how data governance teams can define decision logic
using simple YAML files instead of writing Python code.
"""

import json
from pathlib import Path

from decision_layer import (
    load_decision_from_yaml,
    create_yaml_template,
    validate_yaml_decision,
    DecisionContext,
)


def main():
    """Demonstrate YAML-based decision making"""

    print("🎯 Decision Layer - YAML Interface Example")
    print("=" * 50)

    # Load the YAML decision definition
    yaml_file = Path("examples/approval_decision.yaml")

    if not yaml_file.exists():
        print(f"❌ YAML file not found: {yaml_file}")
        print("Creating template...")
        template = create_yaml_template()
        with open(yaml_file, "w") as f:
            f.write(template)
        print(f"✅ Created template: {yaml_file}")
        return

    # Validate the YAML
    print("🔍 Validating YAML decision definition...")
    with open(yaml_file, "r") as f:
        yaml_content = f.read()

    validation = validate_yaml_decision(yaml_content)

    if validation["valid"]:
        print("✅ YAML validation passed")
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
    else:
        print("❌ YAML validation failed:")
        for error in validation["errors"]:
            print(f"   - {error}")
        return

    print(f"📊 Decision info:")
    print(f"   - Input fields: {validation['info'].get('input_fields', [])}")
    print(f"   - Rule count: {validation['info'].get('rule_count', 0)}")

    # Load the decision function
    print("\n📥 Loading decision function from YAML...")
    decision_function = load_decision_from_yaml(yaml_file)

    # Test cases
    test_cases = [
        {
            "name": "High-risk customer",
            "input": {
                "amount": 15000,
                "customer_score": 450,
                "customer_tier": "standard",
            },
        },
        {
            "name": "Premium customer with good score",
            "input": {
                "amount": 25000,
                "customer_score": 750,
                "customer_tier": "premium",
                "monthly_income": 8000,
            },
        },
        {
            "name": "VIP customer",
            "input": {"amount": 75000, "customer_score": 800, "customer_tier": "vip"},
        },
        {
            "name": "Small personal loan",
            "input": {
                "amount": 3000,
                "customer_score": 650,
                "customer_tier": "standard",
                "employment_status": "employed",
            },
        },
        {
            "name": "Standard tier limit exceeded",
            "input": {
                "amount": 8000,
                "customer_score": 700,
                "customer_tier": "standard",
            },
        },
    ]

    print("\n🧪 Running test cases...")
    print("-" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {json.dumps(test_case['input'], indent=2)}")

        # Create context
        import hashlib
        import uuid
        from datetime import datetime

        input_hash = hashlib.sha256(
            json.dumps(test_case["input"], sort_keys=True).encode()
        ).hexdigest()
        trace_id = str(uuid.uuid4())

        context = DecisionContext(
            function_id="yaml_decision",
            version="1.0",
            input_hash=input_hash,
            timestamp=datetime.now(),
            trace_id=trace_id,
        )

        # Execute decision
        try:
            result = decision_function(test_case["input"], context)
            print(f"Result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("✅ YAML decision example completed!")
    print("\n💡 Key benefits for data governance teams:")
    print("   - No Python programming required")
    print("   - Simple, declarative rule definitions")
    print("   - Easy to understand and maintain")
    print("   - Version control friendly")
    print("   - Business-friendly format")


if __name__ == "__main__":
    main()
