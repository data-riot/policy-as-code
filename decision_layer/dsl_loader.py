import yaml
from decision_layer.executor import resolve_field

def load_yaml_policy(path):
    with open(path) as f:
        data = yaml.safe_load(f)

    rules = data["rules"]
    default = data["default"]

    def decision_fn(obj):

        for rule in rules:
            cond = rule["if"]
            actual_value = resolve_field(obj, cond["field"])
            if actual_value == cond["value"]:
                result = rule["then"].copy()
                result["rule_id"] = rule["id"]
                return result
        return default

    return decision_fn