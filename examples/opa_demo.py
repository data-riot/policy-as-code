#!/usr/bin/env python3
"""
OPA Integration Demo
Shows how Python examples connect to OPA/Rego policies

This demonstrates:
1. Python wrapper for OPA evaluation
2. Integration with existing Rego policies
3. Bridge between Python examples and OPA system
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_opa_evaluation(input_data, policy_path):
    """
    Run OPA evaluation using the OPA binary

    Args:
        input_data: Dictionary with input data
        policy_path: Path to Rego policy directory

    Returns:
        Dictionary with OPA evaluation result
    """
    try:
        # Convert input to JSON
        input_json = json.dumps(input_data)

        # Run OPA evaluation
        cmd = [
            str(project_root / "opa"),
            "eval",
            "-d",
            policy_path,
            "-i",
            "-",
            "data.org.policy_as_code.loan_approval.v1",
        ]

        result = subprocess.run(
            cmd, input=input_json, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            # Parse OPA output
            opa_output = json.loads(result.stdout)
            return {"success": True, "result": opa_output, "raw_output": result.stdout}
        else:
            return {
                "success": False,
                "error": result.stderr,
                "returncode": result.returncode,
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "OPA evaluation timed out"}
    except Exception as e:
        return {"success": False, "error": f"OPA evaluation failed: {str(e)}"}


def opa_loan_approval(input_data):
    """
    Loan approval using OPA/Rego policies

    This shows how the same decision logic can be implemented
    using OPA/Rego instead of pure Python
    """
    print("🔧 OPA Integration Demo")
    print("=" * 50)
    print("📋 Using OPA/Rego policies for loan approval")
    print()

    # Show input data
    print("📊 Input Data:")
    print(f"   Credit Score: {input_data.get('credit_score', 'N/A')}")
    print(f"   Income: ${input_data.get('income', 'N/A'):,}")
    print(f"   Amount: ${input_data.get('amount', 'N/A'):,}")
    print()

    # Run OPA evaluation
    policy_path = str(project_root / "policies" / "rego" / "loan_approval" / "v1.0")

    print("🔍 Running OPA evaluation...")
    result = run_opa_evaluation(input_data, policy_path)

    if result["success"]:
        print("✅ OPA evaluation successful!")
        print()

        # Extract decision from OPA result
        opa_result = result["result"]
        if "result" in opa_result and len(opa_result["result"]) > 0:
            decision_data = opa_result["result"][0]

            print("📋 OPA Decision Result:")
            print(f"   Approved: {decision_data.get('approved', False)}")
            print(f"   Amount: ${decision_data.get('approved_amount', 0):,}")
            print(f"   Interest Rate: {decision_data.get('interest_rate', 0):.1%}")
            print(f"   Risk Level: {decision_data.get('risk_level', 'Unknown')}")

            if not decision_data.get("approved", False):
                print(f"   Reason: {decision_data.get('reason', 'Not specified')}")

            print()
            print("🎉 OPA integration working!")
            return decision_data
        else:
            print("❌ No decision result from OPA")
            return {"approved": False, "reason": "No OPA result"}
    else:
        print("❌ OPA evaluation failed!")
        print(f"   Error: {result['error']}")
        print()
        print("💡 This shows the integration gap that needs to be fixed")
        return {"approved": False, "reason": "OPA evaluation failed"}


def main():
    """Main demo function"""
    print("🚀 Policy as Code - OPA Integration Demo")
    print("=" * 50)
    print("This demo shows the bridge between Python examples and OPA/Rego policies")
    print()

    # Test cases
    test_cases = [
        {
            "name": "John Doe",
            "data": {"credit_score": 750, "income": 75000, "amount": 200000},
        },
        {
            "name": "Jane Smith",
            "data": {"credit_score": 650, "income": 45000, "amount": 150000},
        },
        {
            "name": "Bob Johnson",
            "data": {"credit_score": 800, "income": 100000, "amount": 300000},
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['name']}")
        print("-" * 30)

        result = opa_loan_approval(test_case["data"])

        print()
        print("Next steps:")
        print("1. Fix OPA integration issues")
        print("2. Create unified Python-OPA API")
        print("3. Add OPA examples to learning path")
        print("4. Build production OPA bundles")
        print()

        if i < len(test_cases):
            print("=" * 50)
            print()


if __name__ == "__main__":
    main()
