# 🧠 decision-layer

Treat business logic like code.

---

## 👀 Why

Most companies still make decisions like it's 2005:
- `if` statements scattered across services
- Decision logic in a Notion doc
- Rules buried in dashboards
- No way to test, version, or trace any of it

---

## ✅ What this is

A minimal decision engine that gives you:

- 🧪 Testable decisions
- 🔁 Versioned logic
- 📜 Logged traces
- 🧠 DSL you can read and change

---

## ✨ Try it now

```bash
git clone https://github.com/data-riot/decision-layer
cd decision-layer

pip install -r requirements.txt

python -m decision_layer.cli \
  --policy policies/refund_policy.yaml \
  --input tests/data/sample_order.json
```

You’ll see:

```json
{
  "refund": 100,
  "reason": "Late delivery",
  "rule_id": "late"
}
```

---

## ✅ Run tests

```bash
pytest
```

The test suite runs the policy engine with example input and checks the result.

---

## 🧠 Define a policy

```yaml
# refund_policy.yaml
function: refund_policy
version: v3.2
rules:
  - id: late
    if: { field: "is_late", operator: "==", value: true }
    then: { refund: 100, reason: "Late delivery" }

  - id: damaged
    if: { field: "issue", operator: "==", value: "damaged" }
    then: { refund: 50, reason: "Damaged item" }

default:
  refund: 0
  reason: "Not eligible"
```

---

## 🔍 Output trace format

```json
{
  "input": { "issue": "late", "is_late": true },
  "output": { "refund": 100, "reason": "Late delivery" },
  "version": "v3.2",
  "timestamp": "2025-07-14T12:34:56Z",
  "caller": "cli",
  "rule_id": "late"
}
```

---

## 💡 Use cases

- Refunds
- Risk holds
- Support escalation
- Account flags
- Access control

---

## 🧱 Project structure

```
decision_layer/
  cli.py
  executor.py
  registry.py
  trace_sink.py
  ...

policies/
  refund_policy.yaml

tests/
  test_refund_policy.py
  data/
    sample_order.json
```

---

## ⚠️ Not yet supported

- Nested logic
- Rule priorities
- Boolean expressions (AND/OR)
- Type schemas

This is the starter kit, not the whole platform. Yet!

---

## 📂 Files

- `policies/refund_policy.yaml` — your logic
- `decision_layer/cli.py` — run it
- `tests/test_refund_policy.py` — validate it
- `tests/data/sample_order.json` — example input
- `decision_layer/entities.py` — your input model

---

## 🪪 License

MIT

---

## 🔗 TO DO

- Web UI to browse decisions
- FastAPI wrapper

---

## 🙋‍♂️ Questions?

Open an issue, submit a policy or fork it into your stack.
