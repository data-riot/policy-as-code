def resolve_field(obj, field: str):
    try:
        return getattr(obj, field)
    except AttributeError:
        raise ValueError(f"Field '{field}' not found on object {obj}")

import json
from dataclasses import asdict
from datetime import datetime, timezone

class DecisionExecutor:
    def __init__(self, registry, trace_sink, caller="unknown"):
        self.registry = registry
        self.trace_sink = trace_sink
        self.caller = caller

    def run(self, policy_name, version, input_obj):
        fn = self.registry.get(policy_name, version)
        result = fn(input_obj)

        trace = {
            "input": asdict(input_obj),
            "output": result,
            "version": version,
            "caller": self.caller,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": result.get("rule_id", "unknown")
        }
        if self.trace_sink:
            self.trace_sink.write(trace)
        return result
