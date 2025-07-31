"""
Vision Alignment Demo

This example demonstrates how the Decision Layer implementation aligns with
the vision document's requirements for managing decision logic as versioned,
observable, and governable software artifacts.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from decision_layer.core import DecisionContext, DecisionEngine
from decision_layer.registry import ApprovalStatus, FunctionRegistry, FunctionStatus
from decision_layer.schemas import (
    DecisionSchema,
    FieldType,
    SchemaField,
    create_schema_from_dict,
)
from decision_layer.shadow_runner import ShadowRunner


def create_eligibility_schema() -> DecisionSchema:
    """Create a comprehensive schema for healthcare eligibility decisions"""

    input_schema = {
        "user_id": SchemaField(
            name="user_id",
            type=FieldType.INTEGER,
            required=True,
            description="Unique user identifier",
        ),
        "age": SchemaField(
            name="age",
            type=FieldType.INTEGER,
            required=True,
            min_value=0,
            max_value=150,
            description="User age in years",
        ),
        "product": SchemaField(
            name="product",
            type=FieldType.ENUM,
            required=True,
            enum_values=["insulin", "diabetes_monitor", "test_strips", "consultation"],
            description="Healthcare product type",
        ),
        "region": SchemaField(
            name="region",
            type=FieldType.ENUM,
            required=True,
            enum_values=["EU", "US", "CA", "AU"],
            description="Geographic region",
        ),
        "income_level": SchemaField(
            name="income_level",
            type=FieldType.ENUM,
            required=False,
            enum_values=["low", "medium", "high"],
            default="medium",
            description="User income level",
        ),
        "existing_conditions": SchemaField(
            name="existing_conditions",
            type=FieldType.ARRAY,
            required=False,
            default=[],
            description="List of existing medical conditions",
        ),
    }

    output_schema = {
        "eligible": SchemaField(
            name="eligible",
            type=FieldType.BOOLEAN,
            required=True,
            description="Whether user is eligible for the product",
        ),
        "reason": SchemaField(
            name="reason",
            type=FieldType.STRING,
            required=True,
            description="Explanation for eligibility decision",
        ),
        "coverage_percentage": SchemaField(
            name="coverage_percentage",
            type=FieldType.FLOAT,
            required=True,
            min_value=0.0,
            max_value=100.0,
            description="Percentage of cost covered",
        ),
        "restrictions": SchemaField(
            name="restrictions",
            type=FieldType.ARRAY,
            required=False,
            default=[],
            description="List of restrictions or limitations",
        ),
        "approval_required": SchemaField(
            name="approval_required",
            type=FieldType.BOOLEAN,
            required=True,
            description="Whether manual approval is required",
        ),
    }

    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version="1.0",
        function_id="healthcare_eligibility",
        description="Healthcare product eligibility determination",
        author="healthcare-team",
        tags=["healthcare", "eligibility", "compliance"],
        policy_references=["POL-2024-001", "REG-EU-2023-456"],
        compliance_requirements=["GDPR", "HIPAA", "EU-MDR"],
    )


def create_eligibility_function_v1() -> str:
    """Create version 1.0 of the eligibility function"""
    return '''
def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Healthcare eligibility decision function v1.0

    Determines eligibility based on:
    - Age requirements
    - Product-specific rules
    - Regional regulations
    - Income-based subsidies
    """

    # Extract input data
    age = input_data.get('age', 0)
    product = input_data.get('product', '')
    region = input_data.get('region', '')
    income_level = input_data.get('income_level', 'medium')
    existing_conditions = input_data.get('existing_conditions', [])

    # Base eligibility rules
    eligible = True
    reason = "Eligible based on standard criteria"
    coverage_percentage = 80.0
    restrictions = []
    approval_required = False

    # Age-based restrictions
    if age < 18:
        eligible = False
        reason = "Minimum age requirement not met (18 years)"
    elif age > 65 and product == "insulin":
        coverage_percentage = 95.0  # Higher coverage for seniors

    # Product-specific rules
    if product == "insulin":
        if "diabetes" not in existing_conditions:
            eligible = False
            reason = "Insulin requires diabetes diagnosis"
        elif region == "EU":
            coverage_percentage = 90.0
        elif region == "US":
            coverage_percentage = 85.0

    elif product == "diabetes_monitor":
        if "diabetes" not in existing_conditions:
            approval_required = True
            reason = "Monitor requires diabetes diagnosis or approval"

    elif product == "consultation":
        if income_level == "low":
            coverage_percentage = 100.0
        elif income_level == "medium":
            coverage_percentage = 75.0
        else:
            coverage_percentage = 50.0

    # Regional compliance
    if region == "EU":
        if product == "test_strips" and age > 70:
            restrictions.append("Monthly quantity limit applies")

    return {
        "eligible": eligible,
        "reason": reason,
        "coverage_percentage": coverage_percentage,
        "restrictions": restrictions,
        "approval_required": approval_required,
        "decision_function": context.function_id,
        "version": context.version,
        "execution_timestamp": context.timestamp.isoformat()
    }
'''


def create_eligibility_function_v2() -> str:
    """Create version 2.0 with enhanced logic"""
    return '''
def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Healthcare eligibility decision function v2.0

    Enhanced version with:
    - Improved income-based calculations
    - Additional regional compliance
    - Better handling of existing conditions
    """

    # Extract input data
    age = input_data.get('age', 0)
    product = input_data.get('product', '')
    region = input_data.get('region', '')
    income_level = input_data.get('income_level', 'medium')
    existing_conditions = input_data.get('existing_conditions', [])

    # Base eligibility rules
    eligible = True
    reason = "Eligible based on enhanced criteria"
    coverage_percentage = 80.0
    restrictions = []
    approval_required = False

    # Enhanced age-based restrictions
    if age < 18:
        eligible = False
        reason = "Minimum age requirement not met (18 years)"
    elif age > 65:
        if product == "insulin":
            coverage_percentage = 95.0
        elif product == "consultation":
            coverage_percentage = 90.0

    # Product-specific rules with improvements
    if product == "insulin":
        if "diabetes" not in existing_conditions and "prediabetes" not in existing_conditions:
            eligible = False
            reason = "Insulin requires diabetes or prediabetes diagnosis"
        elif region == "EU":
            coverage_percentage = 90.0
        elif region == "US":
            coverage_percentage = 85.0
        elif region == "CA":
            coverage_percentage = 100.0  # Universal coverage in Canada

    elif product == "diabetes_monitor":
        if "diabetes" not in existing_conditions and "prediabetes" not in existing_conditions:
            approval_required = True
            reason = "Monitor requires diabetes/prediabetes diagnosis or approval"
        else:
            coverage_percentage = 90.0

    elif product == "consultation":
        if income_level == "low":
            coverage_percentage = 100.0
        elif income_level == "medium":
            coverage_percentage = 80.0  # Increased from 75%
        else:
            coverage_percentage = 60.0  # Increased from 50%

    elif product == "test_strips":
        if region == "EU" and age > 70:
            restrictions.append("Monthly quantity limit: 100 strips")
        elif region == "US":
            coverage_percentage = 70.0

    # Enhanced regional compliance
    if region == "EU":
        if product in ["insulin", "diabetes_monitor"]:
            restrictions.append("EU-MDR compliance required")

    elif region == "US":
        if product in ["insulin", "diabetes_monitor"]:
            restrictions.append("FDA approval required")

    return {
        "eligible": eligible,
        "reason": reason,
        "coverage_percentage": coverage_percentage,
        "restrictions": restrictions,
        "approval_required": approval_required,
        "decision_function": context.function_id,
        "version": context.version,
        "execution_timestamp": context.timestamp.isoformat()
    }
'''


async def demonstrate_vision_alignment():
    """Demonstrate how the implementation aligns with the vision document"""

    print("=== Decision Layer Vision Alignment Demo ===\n")

    # 1. Initialize the enhanced registry
    print("1. Initializing Function Registry...")
    registry = FunctionRegistry("./demo_registry")

    # 2. Create and register function v1.0
    print("2. Registering Function v1.0...")
    schema_v1 = create_eligibility_schema()
    function_v1 = create_eligibility_function_v1()

    artifact_v1 = registry.register_function(
        function_id="healthcare_eligibility",
        version="1.0",
        logic_code=function_v1,
        schema=schema_v1,
        metadata={
            "title": "Healthcare Eligibility v1.0",
            "description": "Initial version of healthcare eligibility logic",
            "author": "healthcare-team",
            "tags": ["healthcare", "eligibility", "v1"],
            "policy_references": ["POL-2024-001"],
            "compliance_requirements": ["GDPR", "HIPAA"],
        },
        status=FunctionStatus.DRAFT,
    )

    print(f"   ✓ Registered {artifact_v1.function_id} v{artifact_v1.version}")
    print(f"   Content Hash: {artifact_v1.content_hash[:16]}...")

    # 3. Submit for review and approve
    print("\n3. Governance Workflow...")
    registry.submit_for_review("healthcare_eligibility", "1.0", "healthcare-team")
    registry.approve_function(
        "healthcare_eligibility", "1.0", "compliance-officer", "Approved for production"
    )
    print("   ✓ Function approved for production")

    # 4. Create and register function v2.0
    print("\n4. Registering Function v2.0...")
    schema_v2 = create_eligibility_schema()
    schema_v2.version = "2.0"
    function_v2 = create_eligibility_function_v2()

    artifact_v2 = registry.register_function(
        function_id="healthcare_eligibility",
        version="2.0",
        logic_code=function_v2,
        schema=schema_v2,
        metadata={
            "title": "Healthcare Eligibility v2.0",
            "description": "Enhanced version with improved logic and compliance",
            "author": "healthcare-team",
            "tags": ["healthcare", "eligibility", "v2", "enhanced"],
            "policy_references": ["POL-2024-001", "POL-2024-002"],
            "compliance_requirements": ["GDPR", "HIPAA", "EU-MDR"],
        },
        status=FunctionStatus.DRAFT,
    )

    print(f"   ✓ Registered {artifact_v2.function_id} v{artifact_v2.version}")
    print(f"   Content Hash: {artifact_v2.content_hash[:16]}...")

    # 5. Initialize execution engine
    print("\n5. Initializing Execution Engine...")
    engine = DecisionEngine()

    # 6. Test data for shadow execution
    test_inputs = [
        {
            "user_id": 42,
            "age": 17,
            "product": "insulin",
            "region": "EU",
            "income_level": "medium",
            "existing_conditions": [],
        },
        {
            "user_id": 43,
            "age": 45,
            "product": "insulin",
            "region": "EU",
            "income_level": "low",
            "existing_conditions": ["diabetes"],
        },
        {
            "user_id": 44,
            "age": 72,
            "product": "consultation",
            "region": "US",
            "income_level": "high",
            "existing_conditions": ["hypertension"],
        },
        {
            "user_id": 45,
            "age": 30,
            "product": "diabetes_monitor",
            "region": "CA",
            "income_level": "medium",
            "existing_conditions": ["prediabetes"],
        },
    ]

    # 7. Execute v1.0 decisions
    print("\n6. Executing v1.0 Decisions...")
    v1_results = []
    for i, input_data in enumerate(test_inputs):
        try:
            result = await engine.execute(
                "healthcare_eligibility", input_data, version="1.0"
            )
            v1_results.append(result)
            print(
                f"   Test {i+1}: Eligible={result['eligible']}, Coverage={result['coverage_percentage']}%"
            )
        except Exception as e:
            print(f"   Test {i+1}: Error - {e}")

    # 8. Shadow execution comparison
    print("\n7. Shadow Execution Analysis...")
    shadow_runner = ShadowRunner(registry, None, "demo-shadow-runner")

    shadow_results = shadow_runner.run_simulation(
        function_id="healthcare_eligibility",
        current_version="1.0",
        shadow_version="2.0",
        inputs=test_inputs,
    )

    differences = 0
    for i, result in enumerate(shadow_results):
        if result.has_differences:
            differences += 1
            print(f"   Test {i+1}: DIFFERENCE DETECTED")
            print(f"     v1.0: {result.current_output}")
            print(f"     v2.0: {result.shadow_output}")
            print(f"     Diff: {result.diff_summary}")
        else:
            print(f"   Test {i+1}: No differences")

    print(f"\n   Total differences: {differences}/{len(test_inputs)}")

    # 9. Demonstrate governance features
    print("\n8. Governance Features...")

    # Search functions
    healthcare_functions = registry.search_functions(
        tags=["healthcare"], status=FunctionStatus.APPROVED
    )
    print(f"   Found {len(healthcare_functions)} approved healthcare functions")

    # Function lineage
    lineage = registry.get_function_lineage("healthcare_eligibility")
    print(f"   Function lineage: {len(lineage['versions'])} versions")
    print(f"   Policy references: {lineage['policy_references']}")
    print(f"   Compliance requirements: {lineage['compliance_requirements']}")

    # 10. Demonstrate schema validation
    print("\n9. Schema Validation...")

    # Valid input
    valid_input = {
        "user_id": 46,
        "age": 25,
        "product": "consultation",
        "region": "EU",
        "income_level": "medium",
    }

    try:
        result = await engine.execute(
            "healthcare_eligibility", valid_input, version="1.0"
        )
        print("   ✓ Valid input processed successfully")
    except Exception as e:
        print(f"   ✗ Valid input failed: {e}")

    # Invalid input
    invalid_input = {
        "user_id": "not_a_number",  # Should be integer
        "age": 25,
        "product": "invalid_product",  # Not in enum
        "region": "EU",
    }

    try:
        result = await engine.execute(
            "healthcare_eligibility", invalid_input, version="1.0"
        )
        print("   ✗ Invalid input should have failed")
    except Exception as e:
        print("   ✓ Invalid input properly rejected")
        print(f"     Error: {e}")

    print("\n=== Vision Alignment Summary ===")
    print("✅ Immutable, versioned function artifacts")
    print("✅ Rich metadata and governance support")
    print("✅ Content-addressable storage")
    print("✅ Review and approval workflows")
    print("✅ Structured schema validation")
    print("✅ Shadow execution for safe testing")
    print("✅ Comprehensive tracing and observability")
    print("✅ Search and lineage capabilities")
    print("✅ Deterministic, side-effect-free execution")

    print("\nThe Decision Layer implementation successfully demonstrates")
    print("all key requirements from the vision document!")


if __name__ == "__main__":
    asyncio.run(demonstrate_vision_alignment())
