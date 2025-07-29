#!/usr/bin/env python3
"""
Demo script showcasing the decision layer features
"""

import json
import tempfile
import os
from datetime import datetime

from decision_layer.dsl_loader import load_yaml_policy_with_schema, create_schema_from_example
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.shadow_runner import ShadowRunner
from decision_layer.entities import Customer, Order

def demo_basic_usage():
    """Demo basic decision execution"""
    print("=== Basic Decision Execution ===")
    
    # Load policy with schema
    policy_fn, schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
    
    # Setup registry
    registry = DecisionRegistry()
    registry.register(
        function_id="refund_policy",
        version="v3.2",
        logic=policy_fn,
        schema=schema,
        description="Refund policy with validation",
        author="demo",
        tags=["refund", "finance", "validation"]
    )
    
    # Create test order
    customer = Customer(
        id="123",
        signup_date=datetime(2023, 1, 1),
        status="gold"
    )
    order = Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024, 6, 1),
        delivery_date=datetime(2024, 6, 5),
        issue="late"
    )
    
    # Execute decision
    executor = DecisionExecutor(registry, None, caller="demo")
    result = executor.run("refund_policy", "v3.2", order, enable_validation=True)
    
    print(f"Input: Order A1 with late delivery issue")
    print(f"Output: {json.dumps(result, indent=2)}")
    print()

def demo_schema_validation():
    """Demo schema validation"""
    print("=== Schema Validation ===")
    
    # Load policy with schema
    policy_fn, schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
    
    # Test valid input
    valid_input = {
        "id": "A1",
        "issue": "late",
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "customer": {
            "id": "123",
            "signup_date": "2023-01-01T00:00:00",
            "status": "gold"
        }
    }
    
    from decision_layer.schemas import SchemaValidator
    validator = SchemaValidator(schema)
    
    try:
        validated = validator.validate_input(valid_input)
        print("✅ Valid input passed validation")
        print(f"Validated: {json.dumps(validated, indent=2, default=str)}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Test invalid input
    invalid_input = {
        "id": "A1",
        "issue": "invalid_issue",  # Not in enum
        "customer": {"id": "123"}
    }
    
    try:
        validator.validate_input(invalid_input)
        print("❌ Invalid input should have failed validation")
    except Exception as e:
        print(f"✅ Invalid input correctly rejected: {e}")
    
    print()

def demo_shadow_running():
    """Demo shadow running"""
    print("=== Shadow Running ===")
    
    # Load both policies
    current_fn, current_schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
    shadow_fn, shadow_schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
    
    # Setup registry
    registry = DecisionRegistry()
    registry.register("refund_policy", "v3.2", current_fn, current_schema)
    registry.register("refund_policy", "v3.3", shadow_fn, shadow_schema)
    
    # Create test inputs
    inputs = []
    test_cases = [
        {"issue": "late", "status": "gold"},
        {"issue": "damaged", "status": "bronze"},
        {"issue": "wrong_item", "status": "platinum"},
        {"issue": "none", "status": "silver"}
    ]
    
    for i, case in enumerate(test_cases):
        customer = Customer(
            id=f"customer_{i}",
            signup_date=datetime(2023, 1, 1),
            status=case["status"]
        )
        order = Order(
            id=f"A{i+1}",
            customer=customer,
            order_date=datetime(2024, 6, 1),
            delivery_date=datetime(2024, 6, 5),
            issue=case["issue"]
        )
        inputs.append(order)
    
    # Run shadow analysis
    shadow_runner = ShadowRunner(registry, None, caller="demo")
    analysis = shadow_runner.analyze_regression(
        function_id="refund_policy",
        current_version="v3.2",
        shadow_version="v3.3",
        inputs=inputs
    )
    
    print(f"Shadow Analysis Results:")
    print(f"- Total inputs: {analysis['total_inputs']}")
    print(f"- Successful runs: {analysis['successful_runs']}")
    print(f"- Different outputs: {analysis['different_outputs']}")
    print(f"- Identical outputs: {analysis['identical_outputs']}")
    print()

def demo_function_management():
    """Demo function management features"""
    print("=== Function Management ===")
    
    # Load policies
    policy_fn, schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
    
    # Setup registry with multiple functions
    registry = DecisionRegistry()
    
    # Register multiple versions
    registry.register(
        function_id="refund_policy",
        version="v3.2",
        logic=lambda x: {"refund": 50, "reason": "Old policy"},
        schema=create_schema_from_example({}, {"refund": 0, "reason": ""}, "refund_policy", "v3.2"),
        description="Original refund policy",
        author="team-finance",
        tags=["refund", "legacy"]
    )
    
    registry.register(
        function_id="refund_policy",
        version="v3.4",
        logic=policy_fn,
        schema=schema,
        description="Refund policy with validation",
        author="team-finance",
        tags=["refund", "finance", "validation"]
    )
    
    registry.register(
        function_id="risk_assessment",
        version="v1.0",
        logic=lambda x: {"risk_score": 0.5, "approved": True},
        schema=create_schema_from_example({}, {"risk_score": 0.0, "approved": False}, "risk_assessment", "v1.0"),
        description="Risk assessment for transactions",
        author="team-risk",
        tags=["risk", "security"]
    )
    
    # List functions
    print("All functions:")
    for function_id in registry.list_functions():
        latest = registry.get_latest(function_id)
        versions = registry.list_versions(function_id)
        print(f"- {function_id}: {latest.version} ({', '.join(versions)})")
    
    # Search by tags
    print("\nFunctions tagged 'refund':")
    refund_functions = registry.search(tags=["refund"])
    for func in refund_functions:
        print(f"- {func.function_id}.{func.version}: {func.description}")
    
    # Search by author
    print("\nFunctions by team-finance:")
    finance_functions = registry.search(author="team-finance")
    for func in finance_functions:
        print(f"- {func.function_id}.{func.version}: {func.description}")
    
    print()

def demo_trace_logging():
    """Demo trace logging"""
    print("=== Trace Logging ===")
    
    # Create temporary trace file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        trace_file = f.name
    
    try:
        # Load policy
        policy_fn, schema = load_yaml_policy_with_schema("policies/refund_policy.yaml")
        
        # Setup registry and executor with trace sink
        registry = DecisionRegistry()
        registry.register(
            function_id="refund_policy",
            version="v3.2",
            logic=policy_fn,
            schema=schema
        )
        
        sink = FileSink(trace_file)
        executor = DecisionExecutor(registry, sink, caller="demo")
        
        # Create test order
        customer = Customer(
            id="123",
            signup_date=datetime(2023, 1, 1),
            status="gold"
        )
        order = Order(
            id="A1",
            customer=customer,
            order_date=datetime(2024, 6, 1),
            delivery_date=datetime(2024, 6, 5),
            issue="late"
        )
        
        # Execute decision
        result = executor.run("refund_policy", "v3.2", order, enable_validation=True)
        
        # Read and display trace
        with open(trace_file, 'r') as f:
            trace_line = f.readline().strip()
            trace = json.loads(trace_line)
        
        print("Trace logged:")
        print(f"- Invocation ID: {trace['invocation_id']}")
        print(f"- Function: {trace['function_id']}.{trace['version']}")
        print(f"- Status: {trace['status']}")
        print(f"- Execution time: {trace['execution_time_ms']}ms")
        print(f"- Schema validated: {trace['schema_validated']}")
        print(f"- Input hash: {trace['input_hash']}")
        print(f"- Output hash: {trace['output_hash']}")
        
    finally:
        # Clean up
        os.unlink(trace_file)
    
    print()

def main():
    """Run all demos"""
    print("🧠 Decision Layer Features Demo")
    print("=" * 50)
    print()
    
    demo_basic_usage()
    demo_schema_validation()
    demo_shadow_running()
    demo_function_management()
    demo_trace_logging()
    
    print("✅ All demos completed successfully!")
    print("\nKey Features Demonstrated:")
    print("- Schema validation with type checking and constraints")
    print("- Shadow running for safe testing of logic")
    print("- Function versioning and management")
    print("- Structured trace logging with hashes")
    print("- CLI with multiple commands")
    print("- Backward compatibility with existing policies")

if __name__ == "__main__":
    main() 