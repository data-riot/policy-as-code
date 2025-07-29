import argparse
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

from .dsl_loader import load_yaml_policy, load_yaml_policy_with_schema, create_schema_from_example
from .executor import DecisionExecutor
from .registry import DecisionRegistry
from .trace_sink import FileSink
from .shadow_runner import ShadowRunner
from .entities import Customer, Order

def parse_order(data: Dict[str, Any]) -> Order:
    """Parse order data from JSON"""
    customer_data = data["customer"]
    customer = Customer(
        id=customer_data["id"],
        signup_date=datetime.fromisoformat(customer_data["signup_date"]),
        status=customer_data["status"]
    )
    order = Order(
        id=data["id"],
        customer=customer,
        order_date=datetime.fromisoformat(data["order_date"]),
        delivery_date=datetime.fromisoformat(data["delivery_date"]),
        issue=data["issue"]
    )
    return order

def load_policy_with_schema(policy_path: str, use_schema: bool = True):
    """Load policy with or without schema support"""
    if use_schema:
        try:
            return load_yaml_policy_with_schema(policy_path)
        except Exception as e:
            print(f"Warning: Could not load schema from {policy_path}: {e}")
            print("Falling back to basic policy loading...")
            return load_yaml_policy(policy_path), None
    else:
        return load_yaml_policy(policy_path), None

def run_decision(args):
    """Run a single decision"""
    # Load policy
    policy_fn, schema = load_policy_with_schema(args.policy, args.use_schema)
    
    # Setup registry
    registry = DecisionRegistry()
    
    # Create schema if not provided
    if schema is None and args.use_schema:
        # Create example data for schema inference
        with open(args.input, "r") as f:
            input_data = json.load(f)
        order = parse_order(input_data)
        
        # Run once to get output example
        temp_output = policy_fn(order)
        
        # Create schema from examples
        schema = create_schema_from_example(
            input_example=input_data,
            output_example=temp_output,
            function_id=args.function_id or "unknown",
            version=args.version
        )
    
    # Register function
    if schema:
        registry.register(
            function_id=args.function_id or "refund_policy",
            version=args.version,
            logic=policy_fn,
            schema=schema,
            description=args.description,
            author=args.author,
            tags=args.tags.split(",") if args.tags else []
        )
    else:
        # Legacy registration without schema
        registry.register(
            function_id=args.function_id or "refund_policy",
            version=args.version,
            logic=policy_fn,
            schema=create_schema_from_example({}, {}, args.function_id or "unknown", args.version)
        )
    
    # Setup trace sink
    sink = FileSink(args.trace) if args.trace else None
    executor = DecisionExecutor(registry, sink, caller="cli")
    
    # Load and parse input
    with open(args.input, "r") as f:
        input_data = json.load(f)
    
    order = parse_order(input_data)
    
    # Run decision
    try:
        result = executor.run(
            function_id=args.function_id or "refund_policy",
            version=args.version,
            input_obj=order,
            enable_validation=args.use_schema
        )
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_shadow(args):
    """Run shadow analysis"""
    # Load both policies
    current_fn, current_schema = load_policy_with_schema(args.current_policy, args.use_schema)
    shadow_fn, shadow_schema = load_policy_with_schema(args.shadow_policy, args.use_schema)
    
    # Setup registry
    registry = DecisionRegistry()
    
    # Register both functions
    current_version = args.current_version or "v3.2"
    shadow_version = args.shadow_version or "v3.2"
    
    if current_schema:
        registry.register("refund_policy", current_version, current_fn, current_schema)
    else:
        registry.register("refund_policy", current_version, current_fn, 
                         create_schema_from_example({}, {}, "refund_policy", current_version))
    
    if shadow_schema:
        registry.register("refund_policy", shadow_version, shadow_fn, shadow_schema)
    else:
        registry.register("refund_policy", shadow_version, shadow_fn,
                         create_schema_from_example({}, {}, "refund_policy", shadow_version))
    
    # Setup shadow runner
    sink = FileSink(args.trace) if args.trace else None
    shadow_runner = ShadowRunner(registry, sink, caller="cli-shadow")
    
    # Load test inputs
    inputs = []
    if args.inputs:
        for input_file in args.inputs:
            with open(input_file, "r") as f:
                input_data = json.load(f)
                
                # Handle both single input and array of inputs
                if isinstance(input_data, list):
                    for item in input_data:
                        order = parse_order(item)
                        inputs.append(order)
                else:
                    order = parse_order(input_data)
                    inputs.append(order)
    
    # Run shadow analysis
    if args.mode == "simulation":
        results = shadow_runner.run_simulation(
            function_id="refund_policy",
            current_version=current_version,
            shadow_version=shadow_version,
            inputs=inputs
        )
        
        # Generate analysis
        analysis = shadow_runner.analyze_regression(
            function_id="refund_policy",
            current_version=current_version,
            shadow_version=shadow_version,
            inputs=inputs
        )
        
        if args.report:
            report = shadow_runner.generate_report(analysis)
            with open(args.report, "w") as f:
                f.write(report)
        else:
            print(shadow_runner.generate_report(analysis))
        
        # Show summary
        print(f"\nSummary: {analysis['different_outputs']} differences out of {analysis['total_inputs']} inputs")
        
    elif args.mode == "mirror":
        if len(inputs) != 1:
            print("Error: Mirror mode requires exactly one input", file=sys.stderr)
            sys.exit(1)
        
        result = shadow_runner.run_mirror(
            function_id="refund_policy",
            current_version=current_version,
            shadow_version=shadow_version,
            input_data=inputs[0]
        )
        
        if result.has_differences:
            print("⚠️  Differences detected:")
            print(json.dumps(result.diff_summary, indent=2))
        else:
            print("✅ No differences detected")

def list_functions(args):
    """List registered functions"""
    registry = DecisionRegistry()
    
    # Load and register policies from directory
    if args.policy_dir:
        for filename in os.listdir(args.policy_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                policy_path = os.path.join(args.policy_dir, filename)
                try:
                    policy_fn, schema = load_policy_with_schema(policy_path, args.use_schema)
                    function_id = filename.replace('.yaml', '').replace('.yml', '')
                    
                    if schema:
                        registry.register(function_id, schema.version, policy_fn, schema)
                    else:
                        registry.register(function_id, "v1.0", policy_fn,
                                         create_schema_from_example({}, {}, function_id, "v1.0"))
                except Exception as e:
                    print(f"Warning: Could not load {filename}: {e}")
    
    # List functions
    functions = registry.list_functions()
    if not functions:
        print("No functions registered")
        return
    
    print("Registered Functions:")
    print("====================")
    
    for function_id in functions:
        latest = registry.get_latest(function_id)
        versions = registry.list_versions(function_id)
        
        print(f"\n{function_id}:")
        print(f"  Latest Version: {latest.version}")
        print(f"  Description: {latest.description or 'No description'}")
        print(f"  Author: {latest.author or 'Unknown'}")
        print(f"  Tags: {', '.join(latest.tags) if latest.tags else 'None'}")
        print(f"  All Versions: {', '.join(versions)}")

def validate_schema(args):
    """Validate input against schema"""
    # Load policy with schema
    policy_fn, schema = load_policy_with_schema(args.policy, use_schema=True)
    
    if not schema:
        print("Error: No schema found in policy", file=sys.stderr)
        sys.exit(1)
    
    # Load input
    with open(args.input, "r") as f:
        input_data = json.load(f)
    
    # Validate
    try:
        from .schemas import SchemaValidator
        validator = SchemaValidator(schema)
        validated = validator.validate_input(input_data)
        print("✅ Input validation successful")
        print(json.dumps(validated, indent=2))
    except Exception as e:
        print(f"❌ Input validation failed: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Decision Layer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run decision command
    run_parser = subparsers.add_parser("run", help="Run a decision")
    run_parser.add_argument("--policy", required=True, help="Path to policy YAML file")
    run_parser.add_argument("--input", required=True, help="Path to input JSON file")
    run_parser.add_argument("--output", help="Path to output JSON file")
    run_parser.add_argument("--version", default="v3.2", help="Policy version")
    run_parser.add_argument("--function-id", help="Function ID")
    run_parser.add_argument("--description", help="Function description")
    run_parser.add_argument("--author", help="Function author")
    run_parser.add_argument("--tags", help="Comma-separated tags")
    run_parser.add_argument("--trace", help="Path to trace output")
    run_parser.add_argument("--use-schema", action="store_true", help="Enable schema validation")
    run_parser.set_defaults(func=run_decision)
    
    # Shadow analysis command
    shadow_parser = subparsers.add_parser("shadow", help="Run shadow analysis")
    shadow_parser.add_argument("--current-policy", required=True, help="Current policy file")
    shadow_parser.add_argument("--shadow-policy", required=True, help="Shadow policy file")
    shadow_parser.add_argument("--current-version", help="Current version")
    shadow_parser.add_argument("--shadow-version", help="Shadow version")
    shadow_parser.add_argument("--inputs", nargs="+", required=True, help="Input JSON files")
    shadow_parser.add_argument("--mode", choices=["simulation", "mirror"], default="simulation", help="Shadow mode")
    shadow_parser.add_argument("--trace", help="Path to trace output")
    shadow_parser.add_argument("--report", help="Path to analysis report")
    shadow_parser.add_argument("--use-schema", action="store_true", help="Enable schema validation")
    shadow_parser.set_defaults(func=run_shadow)
    
    # List functions command
    list_parser = subparsers.add_parser("list", help="List registered functions")
    list_parser.add_argument("--policy-dir", help="Directory containing policy files")
    list_parser.add_argument("--use-schema", action="store_true", help="Enable schema validation")
    list_parser.set_defaults(func=list_functions)
    
    # Validate schema command
    validate_parser = subparsers.add_parser("validate", help="Validate input against schema")
    validate_parser.add_argument("--policy", required=True, help="Path to policy YAML file")
    validate_parser.add_argument("--input", required=True, help="Path to input JSON file")
    validate_parser.set_defaults(func=validate_schema)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)

if __name__ == "__main__":
    main()