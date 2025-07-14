import yaml

def load_yaml_policy(path):
    with open(path) as f:
        data = yaml.safe_load(f)

    rules = data["rules"]
    default = data["default"]

    def decision_fn(obj):
        context = obj.__dict__
        for rule in rules:
            cond = rule["if"]
            if context.get(cond["field"]) == cond["value"]:
                result = rule["then"].copy()
                result["rule_id"] = rule["id"]
                return result
        return default

    return decision_fn