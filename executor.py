import json
from dataclasses import asdict
from datetime import datetime

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
            "timestamp": datetime.utcnow().isoformat(),
            "rule_id": result.get("rule_id", "unknown")
        }
        self.trace_sink.write(trace)
        return result
