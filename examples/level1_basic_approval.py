#!/usr/bin/env python3
"""
Level 1: Basic Approval Logic
Learn the fundamentals of Policy as Code

This example demonstrates:
- Simple decision structure
- Basic input validation
- Clear output format
- Error handling
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def basic_approval(input_data):
    """
    Basic approval logic - approve if age >= 18 and income >= 30000

    This is the simplest possible decision function that demonstrates:
    - Input extraction
    - Simple business rules
    - Clear output format
    """
    # Extract input data
    age = input_data.get("age", 0)
    income = input_data.get("income", 0)
    name = input_data.get("name", "Unknown")

    print(f"📋 Processing application for {name}")
    print(f"   Age: {age}")
    print(f"   Income: ${income:,}")

    # Simple business logic
    if age >= 18 and income >= 30000:
        return {
            "approved": True,
            "reason": "Meets basic requirements",
            "details": {"age_check": "Passed", "income_check": "Passed"},
        }
    else:
        reasons = []
        if age < 18:
            reasons.append("Age below 18")
        if income < 30000:
            reasons.append("Income below $30,000")

        return {
            "approved": False,
            "reason": "Does not meet requirements",
            "details": {
                "age_check": "Failed" if age < 18 else "Passed",
                "income_check": "Failed" if income < 30000 else "Passed",
                "specific_issues": reasons,
            },
        }


def main():
    """Run the basic approval example"""
    print("🎓 Level 1: Basic Approval Logic")
    print("=" * 50)
    print("Learning objectives:")
    print("✅ Simple decision structure")
    print("✅ Basic input validation")
    print("✅ Clear output format")
    print("✅ Error handling")
    print()

    # Test cases
    test_cases = [
        {"name": "Alice", "age": 25, "income": 45000},  # Should pass
        {"name": "Bob", "age": 17, "income": 35000},  # Age too young
        {"name": "Carol", "age": 30, "income": 25000},  # Income too low
        {"name": "David", "age": 16, "income": 20000},  # Both fail
    ]

    print("📋 Running test cases...")
    print()

    for i, test_data in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_data['name']}")
        print("-" * 30)

        try:
            result = basic_approval(test_data)

            if result["approved"]:
                print("✅ APPROVED")
                print(f"   Reason: {result['reason']}")
            else:
                print("❌ DENIED")
                print(f"   Reason: {result['reason']}")
                if "specific_issues" in result["details"]:
                    for issue in result["details"]["specific_issues"]:
                        print(f"   - {issue}")

            print()

        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()

    print("🎉 Level 1 completed!")
    print()
    print("Next steps:")
    print("1. Try modifying the age and income requirements")
    print("2. Add more criteria (e.g., employment status)")
    print("3. Move to Level 2: Multi-Criteria Decisions")
    print("4. Check out PROGRESSIVE_EXAMPLES.md for the full learning path")


if __name__ == "__main__":
    main()
