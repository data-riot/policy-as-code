#!/usr/bin/env python3
"""
Simple Policy as Code Demo
A working example that demonstrates basic functionality

This script shows:
1. Basic decision function
2. Input validation
3. Output validation
4. Simple execution
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def simple_loan_approval(input_data):
    """
    Simple loan approval decision function

    This demonstrates basic business logic:
    - Check credit score
    - Check income
    - Return approval decision
    """
    credit_score = input_data.get("credit_score", 0)
    income = input_data.get("income", 0)
    applicant_name = input_data.get("applicant_name", "Unknown")

    print(f"📊 Processing application for {applicant_name}")
    print(f"   Credit Score: {credit_score}")
    print(f"   Income: ${income:,}")

    # Simple business logic
    if credit_score >= 700 and income >= 50000:
        approved_amount = min(income * 3, 500000)
        return {
            "approved": True,
            "reason": "Meets all criteria",
            "approved_amount": approved_amount,
            "interest_rate": 0.05 if credit_score > 750 else 0.07,
        }
    else:
        reasons = []
        if credit_score < 700:
            reasons.append("Credit score below 700")
        if income < 50000:
            reasons.append("Income below $50,000")

        return {"approved": False, "reason": "; ".join(reasons), "approved_amount": 0}


def main():
    """Main demo function"""
    print("🚀 Policy as Code - Simple Demo")
    print("=" * 50)

    # Test data
    test_cases = [
        {"applicant_name": "John Doe", "credit_score": 750, "income": 75000},
        {"applicant_name": "Jane Smith", "credit_score": 650, "income": 45000},
        {"applicant_name": "Bob Johnson", "credit_score": 800, "income": 100000},
    ]

    print("📋 Running test cases...")
    print()

    for i, test_data in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print("-" * 20)

        try:
            # Execute decision
            result = simple_loan_approval(test_data)

            # Display result
            if result["approved"]:
                print(f"✅ APPROVED")
                print(f"   Amount: ${result['approved_amount']:,}")
                print(f"   Interest Rate: {result['interest_rate']:.1%}")
            else:
                print(f"❌ DENIED")
                print(f"   Reason: {result['reason']}")

            print()

        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()

    print("🎉 Demo completed!")
    print()
    print("Next steps:")
    print("1. Try modifying the business logic in simple_loan_approval()")
    print("2. Add more test cases")
    print("3. Try Level 1: python3 examples/level1_basic_approval.py")
    print("4. Read GETTING_STARTED.md for the complete learning path")


if __name__ == "__main__":
    main()
