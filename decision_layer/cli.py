import argparse
import json
import os
from decision_layer.dsl_loader import load_yaml_policy
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.entities import Customer, Order
from datetime import datetime

def parse_order(data):
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

def main():
    parser = argparse.ArgumentParser(description="Run a decision policy")
    parser.add_argument("--policy", required=True, help="Path to policy YAML file")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--version", default="v3.2", help="Policy version")
    parser.add_argument("--trace", help="Optional path to trace output")

    args = parser.parse_args()

    policy_fn = load_yaml_policy(args.policy)

    registry = DecisionRegistry()
    registry.register("refund_policy", args.version, policy_fn)

    sink = FileSink(args.trace) if args.trace else None
    executor = DecisionExecutor(registry, sink, caller="cli")

    with open(args.input, "r") as f:
        input_data = json.load(f)

    order = parse_order(input_data)
    result = executor.run("refund_policy", args.version, order)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()