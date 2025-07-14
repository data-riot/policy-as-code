import argparse
import json
from datetime import datetime
from dsl_loader import load_yaml_policy
from registry import DecisionRegistry
from trace_sink import FileSink
from executor import DecisionExecutor
from entities import Customer, Order

def parse_input(filepath):
    with open(filepath) as f:
        raw = json.load(f)

    customer_data = raw["customer"]
    customer = Customer(
        id=customer_data["id"],
        signup_date=datetime.fromisoformat(customer_data["signup_date"]),
        status=customer_data["status"]
    )

    order = Order(
        id=raw["id"],
        customer=customer,
        order_date=datetime.fromisoformat(raw["order_date"]),
        delivery_date=datetime.fromisoformat(raw["delivery_date"]),
        issue=raw["issue"]
    )

    return order

def main():
    parser = argparse.ArgumentParser(description="Run a decision policy.")
    parser.add_argument("policy", help="Policy name")
    parser.add_argument("version", help="Policy version")
    parser.add_argument("--input", required=True, help="Path to input JSON")

    args = parser.parse_args()

    policy_fn = load_yaml_policy(f"{args.policy}.yaml")

    registry = DecisionRegistry()
    registry.register(args.policy, args.version, policy_fn)

    trace_sink = FileSink("demo_trace.jsonl")
    executor = DecisionExecutor(registry, trace_sink, caller="cli")

    input_data = parse_input(args.input)
    result = executor.run(args.policy, args.version, input_data)

    print("Decision result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()