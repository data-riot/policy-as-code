#!/usr/bin/env python3
"""
Level 1: Multi-Criteria Decisions
Learn to handle complex business rules

This example demonstrates:
- Multiple decision criteria
- Complex business logic
- Detailed output with calculations
- Better error handling
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def loan_approval(input_data):
    """
    Multi-criteria loan approval with detailed business logic

    This demonstrates:
    - Multiple decision criteria
    - Complex calculations
    - Detailed output format
    - Risk assessment
    """
    # Extract input data
    credit_score = input_data.get("credit_score", 0)
    income = input_data.get("income", 0)
    debt_ratio = input_data.get("debt_ratio", 0)
    employment_years = input_data.get("employment_years", 0)
    loan_amount = input_data.get("loan_amount", 0)
    applicant_name = input_data.get("name", "Unknown")

    print(f"📊 Processing loan application for {applicant_name}")
    print(f"   Credit Score: {credit_score}")
    print(f"   Annual Income: ${income:,}")
    print(f"   Debt Ratio: {debt_ratio:.1%}")
    print(f"   Employment Years: {employment_years}")
    print(f"   Requested Amount: ${loan_amount:,}")

    # Initialize result
    result = {
        "approved": False,
        "reason": "",
        "approved_amount": 0,
        "interest_rate": 0,
        "risk_level": "Unknown",
        "criteria_checks": {},
    }

    # Check credit score
    if credit_score < 600:
        result["criteria_checks"]["credit_score"] = "Failed - Too low"
        result["reason"] = "Credit score below minimum requirement (600)"
        return result
    elif credit_score >= 750:
        result["criteria_checks"]["credit_score"] = "Excellent"
        credit_tier = "excellent"
    elif credit_score >= 700:
        result["criteria_checks"]["credit_score"] = "Good"
        credit_tier = "good"
    else:
        result["criteria_checks"]["credit_score"] = "Fair"
        credit_tier = "fair"

    # Check income
    if income < 40000:
        result["criteria_checks"]["income"] = "Failed - Too low"
        result["reason"] = "Income below minimum requirement ($40,000)"
        return result
    else:
        result["criteria_checks"]["income"] = "Passed"

    # Check debt ratio
    if debt_ratio > 0.4:
        result["criteria_checks"]["debt_ratio"] = "Failed - Too high"
        result["reason"] = "Debt ratio exceeds maximum (40%)"
        return result
    else:
        result["criteria_checks"]["debt_ratio"] = "Passed"

    # Check employment history
    if employment_years < 2:
        result["criteria_checks"]["employment"] = "Failed - Too short"
        result["reason"] = "Employment history too short (minimum 2 years)"
        return result
    else:
        result["criteria_checks"]["employment"] = "Passed"

    # All criteria passed - calculate approval
    result["approved"] = True
    result["reason"] = "All criteria met"

    # Calculate approved amount (up to 4x income, max $500k)
    max_amount = min(income * 4, 500000)
    result["approved_amount"] = min(loan_amount, max_amount)

    # Calculate interest rate based on credit tier
    if credit_tier == "excellent":
        result["interest_rate"] = 0.045  # 4.5%
        result["risk_level"] = "Low"
    elif credit_tier == "good":
        result["interest_rate"] = 0.055  # 5.5%
        result["risk_level"] = "Medium"
    else:  # fair
        result["interest_rate"] = 0.065  # 6.5%
        result["risk_level"] = "Medium-High"

    # Adjust for debt ratio
    if debt_ratio > 0.3:
        result["interest_rate"] += 0.005  # Add 0.5% for higher debt

    return result


def main():
    """Run the multi-criteria loan approval example"""
    print("🎓 Level 1: Multi-Criteria Decisions")
    print("=" * 50)
    print("Learning objectives:")
    print("✅ Multiple decision criteria")
    print("✅ Complex business logic")
    print("✅ Detailed output with calculations")
    print("✅ Risk assessment")
    print()

    # Test cases
    test_cases = [
        {
            "name": "Alice Johnson",
            "credit_score": 780,
            "income": 75000,
            "debt_ratio": 0.25,
            "employment_years": 5,
            "loan_amount": 200000,
        },
        {
            "name": "Bob Smith",
            "credit_score": 650,
            "income": 45000,
            "debt_ratio": 0.35,
            "employment_years": 3,
            "loan_amount": 150000,
        },
        {
            "name": "Carol Davis",
            "credit_score": 580,
            "income": 50000,
            "debt_ratio": 0.20,
            "employment_years": 4,
            "loan_amount": 100000,
        },
        {
            "name": "David Wilson",
            "credit_score": 720,
            "income": 35000,
            "debt_ratio": 0.45,
            "employment_years": 1,
            "loan_amount": 120000,
        },
    ]

    print("📋 Running test cases...")
    print()

    for i, test_data in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_data['name']}")
        print("-" * 40)

        try:
            result = loan_approval(test_data)

            if result["approved"]:
                print("✅ APPROVED")
                print(f"   Approved Amount: ${result['approved_amount']:,}")
                print(f"   Interest Rate: {result['interest_rate']:.1%}")
                print(f"   Risk Level: {result['risk_level']}")
            else:
                print("❌ DENIED")
                print(f"   Reason: {result['reason']}")

            # Show criteria checks
            print("   Criteria Checks:")
            for criterion, status in result["criteria_checks"].items():
                print(f"   - {criterion.replace('_', ' ').title()}: {status}")

            print()

        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()

    print("🎉 Level 1 Multi-Criteria completed!")
    print()
    print("Next steps:")
    print("1. Try adding more criteria (e.g., down payment, property type)")
    print("2. Experiment with different risk calculations")
    print("3. Move to Level 2: Domain-Specific Logic")
    print("4. Check out PROGRESSIVE_EXAMPLES.md for the full learning path")


if __name__ == "__main__":
    main()
