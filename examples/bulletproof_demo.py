#!/usr/bin/env python3
"""
Bulletproof Decision Flow Demo
Demonstrates strict Pydantic validation and end-to-end decision flow

This script shows:
1. Strict input validation with detailed error reporting
2. Policy execution with monitoring
3. Output validation
4. Trace record creation and signing
5. Persistent audit logging
6. Trace integrity verification
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from policy_as_code.core.bulletproof_flow import BulletproofDecisionFlow
from policy_as_code.validation.strict_models import (
    validate_eligibility_input,
    validate_eligibility_output,
    EligibilityInput,
    EligibilityOutput,
    DecisionOutcome,
    PersonId,
    PersonIdType,
    Income,
    IncomeSource,
    Residence,
    ResidenceStatus,
    Family,
    Dependent,
    RelationshipType,
    EconomicActivity,
    EmploymentStatus,
    WorkCapacity,
    WorkBarrier,
)


async def sample_eligibility_policy(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sample eligibility policy function

    This demonstrates a real policy that:
    - Checks income thresholds
    - Validates residence status
    - Considers family circumstances
    - Applies complex eligibility rules
    """
    person_id = input_data.get("person_id", {})
    income = input_data.get("income", {})
    residence = input_data.get("residence", {})
    family = input_data.get("family", {})
    economic_activity = input_data.get("economic_activity", {})

    # Extract key values
    monthly_income = income.get("monthly_net_eur", 0)
    residence_status = residence.get("residence_status")
    household_size = family.get("household_size", 1) if family else 1
    dependents = family.get("dependents", []) if family else []
    employment_status = (
        economic_activity.get("employment_status") if economic_activity else None
    )
    work_capacity = (
        economic_activity.get("work_capacity") if economic_activity else None
    )

    # Calculate income thresholds
    base_threshold = 2000.0
    dependent_bonus = 500.0
    total_threshold = base_threshold + (len(dependents) * dependent_bonus)

    # Check basic eligibility criteria
    criteria_met = []
    criteria_not_met = []

    # Income check
    if monthly_income >= total_threshold:
        criteria_met.append("income_threshold_met")
    else:
        criteria_not_met.append("income_insufficient")

    # Residence status check
    if residence_status in ["citizen", "permanent_resident"]:
        criteria_met.append("residence_status_valid")
    else:
        criteria_not_met.append("residence_status_invalid")

    # Employment status check (if applicable)
    if employment_status == "employed":
        criteria_met.append("employment_verified")
    elif employment_status == "unemployed" and work_capacity in ["full", "partial"]:
        criteria_met.append("unemployed_but_work_capable")
    elif employment_status == "disabled" and work_capacity == "none":
        criteria_met.append("disabled_no_work_capacity")
    else:
        criteria_not_met.append("employment_status_issue")

    # Make decision
    if len(criteria_not_met) == 0:
        decision = DecisionOutcome.APPROVED
        confidence = 0.95
        reasoning = [
            f"Monthly income €{monthly_income:,.2f} exceeds threshold €{total_threshold:,.2f}",
            f"Residence status '{residence_status}' is valid",
            f"Household size {household_size} with {len(dependents)} dependents",
            "All eligibility criteria met",
        ]
    elif len(criteria_not_met) == 1 and "employment_status_issue" in criteria_not_met:
        decision = DecisionOutcome.CONDITIONAL_APPROVAL
        confidence = 0.8
        reasoning = [
            f"Monthly income €{monthly_income:,.2f} exceeds threshold €{total_threshold:,.2f}",
            f"Residence status '{residence_status}' is valid",
            "Employment status requires clarification",
            "Conditional approval pending employment verification",
        ]
    else:
        decision = DecisionOutcome.DENIED
        confidence = 0.9
        reasoning = [
            f"Monthly income €{monthly_income:,.2f} below threshold €{total_threshold:,.2f}",
            f"Residence status '{residence_status}' may be invalid",
            "Multiple eligibility criteria not met",
            "Application denied",
        ]

    # Build response
    result = {
        "decision": decision.value,
        "basis": {
            "rule": "comprehensive_eligibility_check",
            "thresholds": {
                "base_threshold": base_threshold,
                "dependent_bonus": dependent_bonus,
                "total_threshold": total_threshold,
                "household_size": household_size,
            },
            "criteria_met": criteria_met,
            "criteria_not_met": criteria_not_met,
        },
        "legal_basis": [
            {
                "law_reference": "https://finlex.fi/fi/laki/ajantasa/2021/20210001",
                "section": "5 §",
                "description": "Income threshold for social assistance eligibility",
            },
            {
                "law_reference": "https://finlex.fi/fi/laki/ajantasa/2021/20210002",
                "section": "3 §",
                "description": "Residence status requirements",
            },
        ],
        "reasoning": reasoning,
        "confidence_score": confidence,
    }

    # Add conditions for conditional approval
    if decision == DecisionOutcome.CONDITIONAL_APPROVAL:
        result["conditions"] = [
            {
                "type": "verification",
                "description": "Provide employment status verification within 30 days",
                "deadline": "2024-02-15T00:00:00Z",
            }
        ]

    # Add appeal info for denied decisions
    if decision == DecisionOutcome.DENIED:
        result["appeal_info"] = {
            "appeal_deadline": "2024-02-15T00:00:00Z",
            "appeal_authority": "Social Security Appeals Board",
            "appeal_process": "Submit written appeal within 30 days",
        }

    return result


async def demonstrate_validation():
    """Demonstrate strict validation with various input scenarios"""
    print("🔍 DEMONSTRATING STRICT VALIDATION")
    print("=" * 50)

    # Test 1: Valid input
    print("\n✅ Test 1: Valid Input")
    valid_input = {
        "person_id": {
            "id": "010190-123A",
            "type": "hetu",
            "verified": True,
            "verification_date": "2024-01-01T00:00:00Z",
        },
        "income": {
            "monthly_net_eur": 2500.0,
            "source": "vero",
            "verification_status": "verified",
            "verification_date": "2024-01-01T00:00:00Z",
            "tax_year": 2024,
        },
        "residence": {
            "municipality_code": "091",
            "residence_status": "citizen",
            "address": "Testikatu 1, 00100 Helsinki",
            "postal_code": "00100",
        },
        "family": {
            "dependents": [
                {
                    "id": "child_1",
                    "relationship": "child",
                    "age": 5,
                    "is_dependent": True,
                }
            ],
            "household_size": 2,
        },
        "economic_activity": {
            "employment_status": "employed",
            "work_capacity": "full",
            "barriers_to_work": [],
        },
    }

    result = validate_eligibility_input(valid_input)
    print(f"Validation result: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    if not result.is_valid:
        for error in result.errors:
            print(f"  - {error['field']}: {error['message']}")

    # Test 2: Invalid input
    print("\n❌ Test 2: Invalid Input")
    invalid_input = {
        "person_id": {"id": "invalid_id", "type": "hetu"},  # Invalid HETU format
        "income": {
            "monthly_net_eur": -100.0,  # Negative income
            "source": "invalid_source",  # Invalid source
        },
        "residence": {
            "municipality_code": "invalid",  # Invalid municipality code
            "residence_status": "invalid_status",  # Invalid status
        },
    }

    result = validate_eligibility_input(invalid_input)
    print(f"Validation result: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    if not result.is_valid:
        for error in result.errors:
            print(f"  - {error['field']}: {error['message']}")

    # Test 3: Boundary values
    print("\n🔬 Test 3: Boundary Values")
    boundary_input = {
        "person_id": {"id": "010190-123A", "type": "hetu"},
        "income": {"monthly_net_eur": 0.0, "source": "vero"},  # Minimum valid income
        "residence": {
            "municipality_code": "000",  # Minimum municipality code
            "residence_status": "citizen",
        },
    }

    result = validate_eligibility_input(boundary_input)
    print(f"Validation result: {'✅ VALID' if result.is_valid else '❌ INVALID'}")


async def demonstrate_bulletproof_flow():
    """Demonstrate bulletproof decision flow"""
    print("\n🛡️ DEMONSTRATING BULLETPROOF DECISION FLOW")
    print("=" * 50)

    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize flow
        flow = BulletproofDecisionFlow(
            storage_path=temp_dir, enable_audit=True, enable_signing=True
        )

        # Register policy
        print("\n📋 Registering Policy")
        flow.register_policy(
            "social_assistance_eligibility",
            "1.0.0",
            sample_eligibility_policy,
            {
                "description": "Social assistance eligibility determination",
                "author": "Policy Team",
                "effective_date": "2024-01-01",
                "legal_basis": [
                    "Social Assistance Act 2021",
                    "Residence Requirements Act 2021",
                ],
            },
        )
        print("✅ Policy registered successfully")

        # Test cases
        test_cases = [
            {
                "name": "High Income Citizen",
                "input": {
                    "person_id": {
                        "id": "010190-123A",
                        "type": "hetu",
                        "verified": True,
                    },
                    "income": {
                        "monthly_net_eur": 3500.0,
                        "source": "vero",
                        "verification_status": "verified",
                    },
                    "residence": {
                        "municipality_code": "091",
                        "residence_status": "citizen",
                    },
                    "family": {
                        "dependents": [
                            {"id": "child_1", "relationship": "child", "age": 8}
                        ],
                        "household_size": 2,
                    },
                    "economic_activity": {
                        "employment_status": "employed",
                        "work_capacity": "full",
                    },
                },
            },
            {
                "name": "Low Income with Dependents",
                "input": {
                    "person_id": {
                        "id": "020190-456B",
                        "type": "hetu",
                        "verified": True,
                    },
                    "income": {
                        "monthly_net_eur": 1800.0,
                        "source": "vero",
                        "verification_status": "verified",
                    },
                    "residence": {
                        "municipality_code": "091",
                        "residence_status": "citizen",
                    },
                    "family": {
                        "dependents": [
                            {"id": "child_1", "relationship": "child", "age": 5},
                            {"id": "child_2", "relationship": "child", "age": 3},
                        ],
                        "household_size": 3,
                    },
                    "economic_activity": {
                        "employment_status": "unemployed",
                        "work_capacity": "partial",
                    },
                },
            },
            {
                "name": "Invalid Input (Should Fail)",
                "input": {
                    "person_id": {"id": "invalid_id", "type": "hetu"},
                    "income": {"monthly_net_eur": -100.0, "source": "invalid_source"},
                    "residence": {
                        "municipality_code": "invalid",
                        "residence_status": "invalid_status",
                    },
                },
            },
        ]

        # Execute test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['name']}")
            print("-" * 30)

            try:
                result = await flow.execute_decision(
                    "social_assistance_eligibility",
                    "1.0.0",
                    test_case["input"],
                    client_id=f"demo_client_{i}",
                    request_id=f"demo_request_{i}",
                )

                if result["success"]:
                    print("✅ Decision executed successfully")
                    print(f"   Trace ID: {result['trace_id']}")
                    print(f"   Decision: {result['decision']['decision']}")
                    print(
                        f"   Confidence: {result['decision']['confidence_score']:.2f}"
                    )
                    print(f"   Execution Time: {result['execution_time_ms']}ms")
                    print(f"   Input Valid: {result['validation']['input_valid']}")
                    print(f"   Output Valid: {result['validation']['output_valid']}")
                    print(f"   Audit Persisted: {result['audit']['audit_persisted']}")
                    print(f"   Signature Valid: {result['audit']['signature_valid']}")
                else:
                    print("❌ Decision execution failed")
                    print(f"   Error Type: {result['error']['type']}")
                    print(f"   Error Message: {result['error']['message']}")
                    print(f"   Input Valid: {result['validation']['input_valid']}")
                    print(f"   Output Valid: {result['validation']['output_valid']}")
                    if result["validation"]["input_errors"]:
                        print("   Input Errors:")
                        for error in result["validation"]["input_errors"]:
                            print(f"     - {error}")
                    if result["validation"]["output_errors"]:
                        print("   Output Errors:")
                        for error in result["validation"]["output_errors"]:
                            print(f"     - {error}")

            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")

        # Verify trace integrity
        print("\n🔗 Verifying Trace Integrity")
        print("-" * 30)
        integrity = flow.verify_trace_integrity()
        print(
            f"Integrity Status: {'✅ OK' if integrity['integrity_ok'] else '❌ BROKEN'}"
        )
        print(f"Total Traces: {integrity['total_traces']}")
        if integrity["broken_chains"]:
            print("Broken Chains:")
            for chain in integrity["broken_chains"]:
                print(f"  - {chain}")

        # Show audit log
        print("\n📊 Audit Log Summary")
        print("-" * 30)
        audit_log = flow.get_audit_log()
        print(f"Total Audit Entries: {len(audit_log)}")

        # Group by action type
        action_counts = {}
        for entry in audit_log:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        for action, count in action_counts.items():
            print(f"  {action}: {count}")

        # Show storage structure
        print("\n📁 Storage Structure")
        print("-" * 30)
        storage_path = Path(temp_dir)
        for item in storage_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(storage_path)
                size = item.stat().st_size
                print(f"  {relative_path} ({size} bytes)")


async def main():
    """Main demonstration function"""
    print("🚀 BULLETPROOF DECISION FLOW DEMONSTRATION")
    print("=" * 60)
    print("This demo shows strict Pydantic validation and")
    print("end-to-end decision flow with audit trails.")
    print("=" * 60)

    # Demonstrate validation
    await demonstrate_validation()

    # Demonstrate bulletproof flow
    await demonstrate_bulletproof_flow()

    print("\n🎉 DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("Key Features Demonstrated:")
    print("✅ Strict Pydantic validation with detailed error reporting")
    print("✅ Immutable decision execution with monitoring")
    print("✅ Output validation and error handling")
    print("✅ Trace record creation and cryptographic signing")
    print("✅ Persistent audit logging")
    print("✅ Trace chain integrity verification")
    print("✅ Comprehensive error handling and recovery")


if __name__ == "__main__":
    asyncio.run(main())
